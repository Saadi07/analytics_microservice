from fastapi import APIRouter, HTTPException, Body
from pymongo import MongoClient
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

router = APIRouter()

def connect_mongo(url, db_name):
    client = MongoClient(url)
    db = client[db_name]
    return db

def calculate_average_power_consumed(data, voltage):
    # Your calculate_average_power_consumed function code here
    current_phase1 = data['CT1']
    current_phase2 = data['CT2']
    current_phase3 = data['CT3']
    power_phase1 = current_phase1 * voltage
    power_phase2 = current_phase2 * voltage
    power_phase3 = current_phase3 * voltage
    average_power = (power_phase1 + power_phase2 + power_phase3) / 3
    return average_power
    pass

@router.post("/")
async def calculate_max_consumption_day(data: dict = Body(...)):
    try:
        MONGO_URL = "mongodb://AMF_DB:W*123123*M@192.168.0.103:27021"
        MONGO_DB_NAME = "test"
        db = connect_mongo(MONGO_URL, MONGO_DB_NAME)

        days = int(data.get('days', 0))

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        cursor = db['cts'].find({
            "mac": "70:b3:d5:fe:4d:09",
            "created_at": {"$gte": start_time, "$lte": end_time}
        })

        data = pd.DataFrame(list(cursor))
        data['created_at'] = pd.to_datetime(data['created_at'])

        voltage = 220  # Voltage in Volts
        data['power_consumed'] = calculate_average_power_consumed(data, voltage)

        daily_average_power = data.groupby(data['created_at'].dt.date)['power_consumed'].mean()

        max_power_date = daily_average_power.idxmax()
        max_power = daily_average_power.loc[max_power_date]

        response_data = {
            "average_power_consumption": daily_average_power.reset_index().to_dict(orient='records'),
            "max_power_date": str(max_power_date),
            "max_power": float(max_power)
        }

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
