from topdoctors.spiders.topdoctors_base import TopdoctorsBaseSpider
from scrapy import Request


class TopdoctorsSpiderES(TopdoctorsBaseSpider):
    name = "topdoctors_es"
    allowed_domains = ["topdoctors.es"]
    start_urls = ["https://www.topdoctors.es/sitemap/especialistas"]
    custom_settings = {
        "ITEM_PIPELINES": {
            'topdoctors.pipelines.TopdoctorsSqlitePipeline': 300,
            'topdoctors.pipelines.TopdoctorsSqliteXLSXEporter': 100},
        "DATABASE_URL": 'sqlite:///db/topdoctors_es.db',
        "XLSX_FILE_PATH": 'db/topdoctors_es_{date}.xlsx',
        "XLSX_SHEET_NAME": 'topdoctors_es'}


class TopdoctorsSpiderIT(TopdoctorsBaseSpider):
    name = "topdoctors_it"
    allowed_domains = ["topdoctors.it"]
    start_urls = ["https://www.topdoctors.it/sitemap/specializzazioni-mediche"]
    custom_settings = {
        "ITEM_PIPELINES": {
            'topdoctors.pipelines.TopdoctorsSqlitePipeline': 300,
            'topdoctors.pipelines.TopdoctorsSqliteXLSXEporter': 100},
        "DATABASE_URL": 'sqlite:///db/topdoctors_it.db',
        "XLSX_FILE_PATH": 'db/topdoctors_it_{date}.xlsx',
        "XLSX_SHEET_NAME": 'topdoctors_it'}


class TopdoctorsSpiderUK(TopdoctorsBaseSpider):
    name = "topdoctors_uk"
    allowed_domains = ["topdoctors.co.uk"]
    start_urls = ["https://www.topdoctors.co.uk/sitemap/specialists"]
    custom_settings = {
        "ITEM_PIPELINES": {
            'topdoctors.pipelines.TopdoctorsSqlitePipeline': 300,
            'topdoctors.pipelines.TopdoctorsSqliteXLSXEporter': 100},
        "DATABASE_URL": 'sqlite:///db/topdoctors_uk.db',
        "XLSX_FILE_PATH": 'db/topdoctors_uk_{date}.xlsx',
        "XLSX_SHEET_NAME": 'topdoctors_uk'}


class TopdoctorsSpiderPartial(TopdoctorsBaseSpider):
    # Useful for testing
    # Allows to start scraping from any spider function
    name = "topdoctors_partial"
    allowed_domains = ["topdoctors.it", "topdoctors.es", "topdoctors.co.uk"]
    start_urls = [
        "https://www.topdoctors.it/dottor/gabriele-fontana-doctor",
        "https://www.topdoctors.es/doctor/josep-miquel-viladoms-fuster",
        "https://www.topdoctors.co.uk/doctor/harsha-kariyawasam"]
    custom_settings = {
        "ITEM_PIPELINES": {
            'topdoctors.pipelines.TopdoctorsSqlitePipeline': 300,
            'topdoctors.pipelines.TopdoctorsSqliteXLSXEporter': 100},
        "DATABASE_URL": 'sqlite:///db/topdoctors_test.db',
        "XLSX_FILE_PATH": 'db/topdoctors_test_{date}.xlsx',
        "XLSX_SHEET_NAME": 'test'}

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, callback=self.parse_doctor)
