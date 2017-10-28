import json
from copy import deepcopy

from scrapy import Spider
from scrapy import Request, FormRequest

from scrapy.http import HtmlResponse
from scrapy.selector import Selector

from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose, TakeFirst

from topdoctors.items import DoctorItem, FacilityItem


class TopdoctorsBaseSpider(Spider):

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse_specialization)

    def parse_specialization(self, response):
        for link in response.xpath('//a[@class="azul"]/@href'):
            url = response.urljoin(link.extract())
            yield Request(url, callback=self.parse_doctor_list)

    def parse_doctor_list(self, response):
        doc_links = response.xpath(
            '//section[contains(@class, "item")]'
            '//a[@class="h3 item_name"][1]/@href')
        for link in doc_links:
            url = response.urljoin(link.extract())
            yield Request(url, callback=self.parse_doctor)

        # pagination
        pages = response.xpath(
            '//ul[@class="pagination"]'
            '//a[@aria-label="Next"]/@href')
        for next_page in pages:
            url = response.urljoin(next_page.extract())
            yield Request(
                url, callback=self.parse_doctor_list)

    def parse_doctor(self, response):
        doc_loader = ItemLoader(item=DoctorItem(), response=response)
        doc_loader.add_value('url', response.url)
        media_loader = doc_loader.nested_xpath(
            '//div[contains(@class,"media-body")]')
        media_loader.add_xpath('title', './h1[@itemprop="name"]/text()')
        media_loader.add_xpath('title', './h1[@class="h3"]/text()')
        media_loader.add_xpath('name', './h1[@itemprop="name"]/text()')
        media_loader.add_xpath('name', './h1[@class="h3"]/text()')

        media_loader.add_xpath('indentity_number', './p/text()')

        media_loader.add_xpath(
            'specialization',
            '(./h2/a/text())|'
            '(./h2/a/span[@class="text-muted"]/text())')
        doc_loader.add_value('photo_link', response.url)
        doc_loader.add_xpath(
            'photo_link',
            '//img[@class="photo_premium_item"]/@src')
        doc_loader.add_xpath(
            'services',
            '//i[contains(@class, "stethoscope")]/ancestor::section[1]'
            '//li/a/text()')
        doc_loader.add_xpath(
            'about',
            '//section[contains(@class,"item_description")]/p/text()')
        doc_loader.add_xpath(
            'email',
            '//script[contains(text(),"email_consulta")]/text()',
            re='email_consulta = \"(?P<extract>.*)\";')
        doc_loader.add_xpath(
            'insurance_companies',
            '//ul[@id="seguro_medico"]//li[@class="item"]/text()')
        doc_loader.add_xpath(
            'insurance_companies',
            '//ul[@id="seguro_medico"]//li[@class="item"]/a/text()')

        form_dataset = self.get_forms_data(response)
        # If facilities exist
        if form_dataset:
            # Save facility quantity
            doc_loader.add_value('_facilities_to_check', len(form_dataset))
            for form_data in form_dataset:

                # Get facility name, phone address,
                fac_loader = ItemLoader(item=FacilityItem(), response=response)
                fac_code = form_data['id_address']
                fac_loader.add_xpath(
                    'phone',
                    '//option[@value="{}"]/@data-telf'.format(fac_code))
                fac_loader.add_xpath(
                    'name',
                    '//option[@value="{}"]/text()'.format(fac_code))
                html_response = HtmlResponse(
                    url=response.url,
                    body=fac_loader.get_xpath(
                        '//option[@value="{}"]/@data-content'.format(fac_code),
                        TakeFirst()),
                    encoding='utf-8')
                fac_loader.selector = Selector(response=html_response)
                fac_loader.add_xpath(
                    'street',
                    '//span[@class="text-muted"]/text()')
                fac_loader.add_xpath(
                    'city',
                    '//span[@class="text-muted"]/text()')

                # Send Item loaders with request
                meta = {'doc_loader': doc_loader, 'fac_loader': fac_loader}
                # Make request to find out appointment status
                yield FormRequest(response.urljoin('/getWeek'),
                                  formdata=form_data,
                                  callback=self.parse_calendar,
                                  meta=meta,
                                  dont_filter=True)
        else:
            fac_loader = ItemLoader(item=FacilityItem(), response=response)
            fac_loader.add_value('appointment', False)
            fac_loader.load_item()
            # Add facility item to doctor item
            doc_loader.add_value('facilities', fac_loader.item)
            yield doc_loader.load_item()

    def parse_calendar(self, response):
        doc_loader = response.meta['doc_loader']
        fac_loader = response.meta['fac_loader']
        loader = ItemLoader(response=response)
        # Check appointment
        fac_loader.add_value(
            'appointment', bool(loader.get_xpath('//a[@class="get_week"]')))
        fac_loader.load_item()
        # Add facility item to doctor item
        doc_loader.add_value('facilities', fac_loader.item)
        # Decrement counter of checked calendars
        to_check = doc_loader.get_output_value('_facilities_to_check')
        doc_loader.replace_value(
            '_facilities_to_check', to_check, lambda v: v - 1)
        # Return doctor item if all facilities are checked
        if doc_loader.get_output_value('_facilities_to_check') == 0:
            yield doc_loader.load_item()

    def get_forms_data(self, response):
        '''Returns formdata for POST request'''

        il = ItemLoader(response=response)
        facilities_ids = il.get_xpath(
            '//script[contains(text(),"$(\'#appointment_book_selector\')'
            '.on(\'change\', function()")]/text()',
            Compose(TakeFirst(), lambda v: json.loads(v), dict.keys, list),
            re='var mutua = \'(.*)\';')

        # Return if there aren't any facilities
        if not facilities_ids:
            return None

        doctor_id = il.get_xpath(
            '//script[@class="gtmanager"]/text()',
            Compose(TakeFirst(), str.strip, lambda v: v.strip('\'')),
            re='{\'ProfId\':(.*)}\);')

        form_data = {
            "id_address": "",
            "id_treatment": "",
            "id_seguro":
                il.get_xpath(
                    '//input[contains(@id,"idSeguro")]/@value',
                    TakeFirst()),
            "fecha":
                il.get_xpath(
                    '//input[contains(@id,"actualDay")]/@value',
                    TakeFirst()),
            "id_doctor": doctor_id,
            "dias":
                il.get_xpath(
                    '//input[contains(@id,"dias")]/@value',
                    TakeFirst()),
            "type": "a",
            "filas":
                il.get_xpath(
                    '//input[contains(@id,"filas")]/@value',
                    TakeFirst()),
            "modal": "1",
            "tipoDoctor":
                il.get_xpath(
                    '//input[contains(@id,"tipoDoctor")]/@value',
                    TakeFirst()),
            "isPop": "false",
            "frame": "0"}

        forms_data = []
        for f_id in facilities_ids:
            fd = deepcopy(form_data)
            fd['id_address'] = f_id
            forms_data.append(fd)
        return forms_data
