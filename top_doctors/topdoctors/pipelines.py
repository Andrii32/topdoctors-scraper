# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from collections import OrderedDict
import datetime

import xlsxwriter

from scrapy.exceptions import DropItem

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .model import Base
from .model import (
    Service, Doctor, Title, Specialization,
    Facility, Appointment, Insurance_company, City)


class TopdoctorsSqlitePipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.database_path = settings.get('DATABASE_URL')

    def create_engine(self):
        engine = create_engine(self.database_path)
        return engine

    def create_tables(self, engine):
        Base.metadata.create_all(engine, checkfirst=True)

    def create_session(self, engine):
        session = sessionmaker(bind=engine)()
        return session

    def open_spider(self, spider):
        engine = self.create_engine()
        self.create_tables(engine)
        self.session = self.create_session(engine)

        self.spider_start_date = datetime.date.today()

    def get_or_create(self, model, filters=None, **kwargs):
        if not filters:
            filters = kwargs
        instance = self.session.query(model).filter_by(**filters).first()
        if instance:
            return instance, False
        else:
            instance = model(**kwargs)
            self.session.add(instance)
            return instance, True

    def update_model(self, object, **kwargs):
        for name, value in kwargs.items():
            setattr(object, name, value)
        return True

    def process_item(self, item, spider):
        # ist of required fields
        required_fields = ['name', 'url']
        if not all(field in item for field in required_fields):
            raise DropItem(
                "Item not contains one of required fields {}".format(
                    ', '.join(required_fields)))

        # Title
        title, _ = self.get_or_create(
            Title, name=item.get('title'))

        # Specialization
        specialization, _ = self.get_or_create(
            Specialization, name=item.get('specialization'))

        # Service
        if item.get('services'):
            services = [self.get_or_create(
                Service, name=service)[0] for service in item.get('services')]
        else:
            services = []

        # Insurance companies
        if item.get('insurance_companies'):
            insurance_companies = [self.get_or_create(
                Insurance_company, name=s)[0] for s in item.get('insurance_companies')]
        else:
            insurance_companies = []

        # Facility
        facilities = []
        for f in item.get('facilities', []):
            city, _ = self.get_or_create(City, name=f.get('city'))
            facility, _ = self.get_or_create(Facility,
                                             name=f.get('name'),
                                             phone=f.get('phone'),
                                             street=f.get('street'),
                                             city=city)
            facilities.append(facility)

        # Doctor
        doctor_params = {
            'name': item.get('name'),
            'title': title,
            'email': item.get('email'),
            'indentity_number': item.get('indentity_number'),
            'specialization': specialization,
            'services': services,
            'insurance_companies': insurance_companies,
            'facilities': facilities,
            'about': item.get('about'),
            'photo_link': item.get('photo_link'),
            'url': item.get('url'),
        }

        doctor, is_created = self.get_or_create(
            Doctor, filters={'url': item.get('url')}, **doctor_params)
        # If doctor aklready exist (checked by url)
        if not is_created:
            self.update_model(doctor, **doctor_params)
            self.session.commit()

        # Appointment
        facilities = item.get('facilities', [])
        if facilities:
            for f in facilities:
                city, _ = self.get_or_create(City, name=f.get('city'))
                facility, _ = self.get_or_create(
                    Facility,
                    name=f.get('name'),
                    phone=f.get('phone'),
                    street=f.get('street'),
                    city=city)

                appointment_params = {
                    'status': f.get('appointment'),
                    'date': self.spider_start_date,
                    'doctor': doctor,
                    'facility': facility
                }
                appointment = Appointment()
                appointment, _ = self.get_or_create(
                    Appointment, **appointment_params)
                self.session.commit()
        else:
            appointment_params = {
                'status': None,
                'date': self.spider_start_date,
                'doctor': doctor,
                'facility': None
            }
            appointment = Appointment()
            appointment, _ = self.get_or_create(
                Appointment, **appointment_params)
            self.session.commit()
        return item

    def close_spider(self, spider):
        self.session.commit()


class TopdoctorsSqliteXLSXEporter(object):
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def __init__(self, settings):
        self.database_path = settings.get('DATABASE_URL')

        self.file_path = settings.get('XLSX_FILE_PATH', 'default.xlsx')
        self.sheet_name = settings.get('XLSX_SHEET_NAME', 'default')

    def create_engine(self):
        engine = create_engine(self.database_path)
        return engine

    def create_tables(self, engine):
        Base.metadata.create_all(engine, checkfirst=True)

    def create_session(self, engine):
        session = sessionmaker(bind=engine)()
        return session

    def open_spider(self, spider):
        self.start_date = datetime.date.today()

        engine = self.create_engine()
        self.create_tables(engine)
        self.session = self.create_session(engine)

        self.workbook = xlsxwriter.Workbook(
            self.file_path.format(date=self.start_date.strftime('%d.%m.%Y')))
        self.worksheet = self.workbook.add_worksheet(self.sheet_name)

    def gen_info_lines(self):
        # Extract dates
        dates = self.session.query(Appointment.date).distinct()
        '''
        list(*zip(*result)) converts
        'sqlalchemy.util._collections.result' to list

        Example:
            [(True,), (True,), (True,), (True,), (True,), (True,), (True,)] ->
            [True, True, True, True, True, True, True]
        '''
        dates = list(*zip(*dates))
        dates = sorted(dates)

        for doctor in self.session.query(Doctor).all():
            line = OrderedDict()
            # Prepare doctors
            line.update({
                'id': doctor.id,
                'Prof': doctor.title.name,
                'Name': doctor.name,
                'Specialization': doctor.specialization.name,
                'Services': ';'.join(s.name for s in doctor.services),
                'Identity number': doctor.indentity_number,
                'Insurance companies': ';'.join(
                    s.name for s in doctor.insurance_companies),
                'Photo': doctor.photo_link,
                'About': doctor.about,
                'URL': doctor.url})

            # Prepare facilities
            facilities = doctor.facilities
            if facilities:
                name = facilities[0].name
                street = facilities[0].street
                city = facilities[0].city.name if facilities[0].city else None
                phone = facilities[0].phone

                line.update({
                    'Facility name': name,
                    'Street': street,
                    'City': city,
                    'Phone': phone})
            else:
                line.update({
                    'Facility name': None,
                    'Street': None,
                    'City': None,
                    'Phone': None})

            # Appointments
            for date in dates:
                statuses = self.session.query(Appointment.status).filter_by(
                    doctor_id=doctor.id, date=date)
                statuses = list(*zip(*statuses))
                # Existing no one apointment status for this date means
                # that current doctor wasn't scraped at this date, so
                # --- appointments = None
                # instead of
                # --- appointments = sum(statuses)
                are_statuses = bool(statuses) and set(statuses).pop() is not None
                if are_statuses:
                    line.update(
                        {date.strftime("%d.%m.%Y"): sum(statuses)})
                else:
                    line.update(
                        {date.strftime("%d.%m.%Y"): None})

            yield line

    def close_spider(self, spider):
        header = next(self.gen_info_lines()).keys()
        self.worksheet.write_row(0, 0, header)

        for index, line_info in enumerate(self.gen_info_lines()):
            self.worksheet.write_row(index + 1, 0, line_info.values())

        self.workbook.close()
