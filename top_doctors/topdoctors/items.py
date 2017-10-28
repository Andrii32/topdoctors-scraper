# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import urllib.parse as parse

from scrapy import Item, Field
from scrapy.loader.processors import (
    MapCompose, Compose, Join, TakeFirst)


def urljoin(links=None):
    try:
        base, path = links
        return parse.urljoin(base, path)
    except ValueError:
        return None


class DoctorItem(Item):
    url = Field(
        output_processor=TakeFirst())
    title = Field(
        input_processor=(
            MapCompose(str.strip,)),
        output_processor=(
            Compose(
                TakeFirst(),
                lambda v: v.split()[0],
                str.strip,
                lambda v: v.strip('.'))))
    name = Field(
        input_processor=(
            MapCompose(
                str.strip,
                lambda v: ' '.join(v.split()[1:]))),
        output_processor=(
            Compose(TakeFirst(), str.strip)))
    specialization = Field(
        input_processor=(MapCompose(str.strip)),
        output_processor=Compose(TakeFirst(), str.strip))
    photo_link = Field(
        output_processor=Compose(urljoin))
    services = Field(
        input_processor=MapCompose(str.strip))
    indentity_number = Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst())
    about = Field(
        output_processor=Compose(TakeFirst(), str.strip))
    email = Field(
        output_processor=TakeFirst())
    facilities = Field()
    _facilities_to_check = Field(
        output_processor=TakeFirst())
    insurance_companies = Field(output_processor=MapCompose(str.strip))


class FacilityItem(Item):
    name = Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst())
    phone = Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst())
    street = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Compose(
            TakeFirst(), lambda v: v.split(',')[:-1],
            MapCompose(str.strip), Join()))
    city = Field(
        input_processor=MapCompose(str.strip),
        output_processor=Compose(
            TakeFirst(), lambda v: v.split(',')[-1], str.strip))
    appointment = Field(
        output_processor=TakeFirst())
