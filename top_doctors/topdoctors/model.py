from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Table, Column, ForeignKey, Integer,
                        String, Date, Boolean, Text)
from sqlalchemy.orm import relationship

Base = declarative_base()

# Todo connect doctors and facilities
# http://docs.sqlalchemy.org/en/latest/orm/basic_relationships.html


class Appointment(Base):
    __tablename__ = 'appointment'
    id = Column(Integer, primary_key=True)

    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    doctor = relationship("Doctor")

    facility_id = Column(Integer, ForeignKey('facilities.id'))
    facility = relationship("Facility")

    status = Column(Boolean())
    date = Column(Date())


DoctorFacilities = Table(
    'doctor_facilitties', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('doctor_id', Integer, ForeignKey('doctors.id')),
    Column('facility_id', Integer, ForeignKey('facilities.id')))


class City(Base):
    __tablename__ = 'cities'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))


class Facility(Base):
    __tablename__ = 'facilities'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    phone = Column(String(250))
    street = Column(String(250))

    city_id = Column(Integer, ForeignKey('cities.id'))
    city = relationship("City")

    doctors = relationship(
        "Doctor", secondary=DoctorFacilities, back_populates="facilities")


DoctorServices = Table(
    'doctor_services', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('doctor_id', Integer, ForeignKey('doctors.id')),
    Column('service_id', Integer, ForeignKey('services.id')))

DoctorInsurance_companies = Table(
    'doctor_insurance_companies', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('doctor_id', Integer, ForeignKey('doctors.id')),
    Column('insurance_companies_id',
           Integer,
           ForeignKey('insurance_companies.id')))


class Service(Base):
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))


class Insurance_company(Base):
    __tablename__ = 'insurance_companies'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))


class Doctor(Base):
    __tablename__ = 'doctors'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))

    title_id = Column(Integer, ForeignKey('titles.id'))
    title = relationship("Title")

    specialization_id = Column(Integer, ForeignKey('specializations.id'))
    specialization = relationship("Specialization")

    services = relationship("Service", secondary=DoctorServices)
    insurance_companies = relationship(
        "Insurance_company", secondary=DoctorInsurance_companies)

    facilities = relationship(
        "Facility", secondary=DoctorFacilities, back_populates="doctors")

    about = Column(Text())
    email = Column(String(250))
    indentity_number = Column(String(250))
    photo_link = Column(String(250))

    url = Column(String(250), nullable=False)


class Title(Base):
    __tablename__ = 'titles'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))


class Specialization(Base):
    __tablename__ = 'specializations'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
