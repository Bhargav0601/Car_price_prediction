from sqlalchemy.orm import Session
from datetime import date
from typing import List
from datetime import datetime
from . import models, schemas


class CarDetailsRepo:
    def create(db: Session, segement: schemas.Cardetails):
        db_item = models.vehicle_details(
            year=segement.year,
            km_driven=segement.km_driven,
            seats=segement.seats,
            mileage=segement.mileage,
            engine=segement.engine,
            max_power=segement.max_power,
            car_company_name=segement.car_company_name,
            fuel=segement.fuel,
            transmission=segement.transmission,
            owner=segement.owner,
            predicted_price=segement.predicted_price,
            timestamp=segement.timestamp,
            source=segement.source,
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    def get_by_date_range(
        db: Session, start_date: date, end_date: date, source
    ) -> List[schemas.Cardetails]:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        return (
            db.query(models.vehicle_details)
            .filter(
                models.vehicle_details.timestamp >= start_datetime,
                models.vehicle_details.timestamp <= end_datetime,
                models.vehicle_details.source == source,
            )
            .all()
        )

    def get_by_date_range_all(
        db: Session, start_date: date, end_date: date
    ) -> List[schemas.Cardetails]:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        return (
            db.query(models.vehicle_details)
            .filter(
                models.vehicle_details.timestamp >= start_datetime,
                models.vehicle_details.timestamp <= end_datetime,
            )
            .all()
        )
