from sqlalchemy import Column, Integer, String, Float, DateTime
import datetime
from db import Base


class vehicle_details(Base):
    __tablename__ = "car_details"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    year = Column(Integer, nullable=True, unique=False)
    km_driven = Column(Integer, nullable=True, unique=False)
    seats = Column(Integer, nullable=True, unique=False)
    mileage = Column(Float, nullable=True, unique=False)
    engine = Column(Integer, nullable=True, unique=False)
    max_power = Column(Float, nullable=True, unique=False)
    car_company_name = Column(String(80), nullable=False, unique=False)
    fuel = Column(String(80), nullable=False, unique=False)
    transmission = Column(String(80), nullable=False, unique=False)
    owner = Column(String(80), nullable=False, unique=False)
    predicted_price = Column(Float, nullable=True, unique=False)
    source = Column(String(80), nullable=False, unique=False)
