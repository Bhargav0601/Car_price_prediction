from datetime import datetime
from pydantic import BaseModel


class VehicleCreate(BaseModel):
    car_company_name: str
    year: int
    km_driven: int
    fuel: str
    transmission: str
    owner: str
    mileage: float
    engine: int
    seats: int
    max_power: float


class Cardetails(BaseModel):
    timestamp: datetime
    year: int
    km_driven: int
    seats: int
    mileage: float
    engine: int
    max_power: float
    car_company_name: str
    fuel: str
    transmission: str
    owner: str
    predicted_price: float
    source: str


class Config:
    orm_mode = True
