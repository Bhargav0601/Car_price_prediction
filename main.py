from datetime import date

import pandas as pd
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import sql_app.models as models

from car_price.inference import make_predictions
from db import get_db, engine
from sql_app.repositories import CarDetailsRepo

app = FastAPI(
    title="Car Price Prediction",
    description=" Swagger at 5001 and Sqlalchemy orm used"
)
models.Base.metadata.create_all(bind=engine)


class DataItem(BaseModel):
    data: list


@app.get("/past-predictions")
async def past_predictions(
    start_date: date = Query(
        ..., description="The start date of the query range"),
    end_date: date = Query(..., description="The end date of the query range"),
    db: Session = Depends(get_db),
    source: str = Query(None),
):
    try:
        if source == "all":
            predictions = CarDetailsRepo.get_by_date_range_all(db, start_date,
                                                               end_date)
        else:
            predictions = CarDetailsRepo.get_by_date_range(
                db, start_date, end_date, source
            )
        data = [
            {
                "year": item.year,
                "km_driven": item.km_driven,
                "seats": item.seats,
                "mileage": item.mileage,
                "engine": item.engine,
                "max_power": item.max_power,
                "car_company_name": item.car_company_name,
                "fuel": item.fuel,
                "transmission": item.transmission,
                "owner": item.owner,
                "predicted_price": item.predicted_price,
                "timestamp": item.timestamp,
                "source": item.source,
            }
            for item in predictions
        ]

        # Convert the list of dictionaries into a DataFrame
        df = pd.DataFrame(data)
        df_dict = df.to_dict(orient="records")
        if not predictions:
            # If no data is found, return a custom message
            return JSONResponse(
                content={"message": "There is no data in between this range"},
                status_code=404,
            )
        return df_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/")
async def make_prediction(
    vehicle_data: DataItem, db: Session = Depends(get_db), source: str =
    Query(None)
):
    if not vehicle_data:
        raise HTTPException(status_code=400, detail="No input data provided.")

    try:
        # Convert list of Pydantic models to list of dictionaries
        df = pd.DataFrame(vehicle_data.data)
        predictions = make_predictions(df)
        df["predicted_price"] = predictions
        df["timestamp"] = datetime.now()
        df["year"] = df["year"].astype(int)
        df["source"] = source
        df = df[
            [
                "year",
                "km_driven",
                "seats",
                "mileage",
                "engine",
                "max_power",
                "car_company_name",
                "fuel",
                "transmission",
                "owner",
                "predicted_price",
                "timestamp",
                "source",
            ]
        ]
        df.to_sql("car_details", engine, if_exists="append", index=False)
        print("df is", df)
        df["timestamp"] = df["timestamp"].apply(
            lambda x: x.strftime('%Y-%m-%dT%H:%M:%S'))
        df_dict = df.to_dict(
            orient="records"
        )

        # Return JSON response with the data
        return JSONResponse(content={"data": df_dict})
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during prediction: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run("main:app", port=5001, host="0.0.0.0", reload=True)
