from fastapi import APIRouter, HTTPException
from fastapi.openapi.models import Info
from datetime import datetime, timedelta
from pymongo import MongoClient
import pandas as pd

router = APIRouter()

def calculate_average_current(data):
    if data.empty:
        return None
    average_current = data[['CT1', 'CT2', 'CT3']].mean(axis=1)
    return average_current

def connect_mongo(url, db_name):
    client = MongoClient(url)
    db = client[db_name]
    return db

def get_data_for_day(db, current_day_start, current_day_end):
    cursor_current = db['cts'].find({
        "mac": "70:b3:d5:fe:4d:09",
        "created_at": {"$gte": current_day_start, "$lt": current_day_end}
    })

    data_current = pd.DataFrame(list(cursor_current))
    data_current['created_at'] = pd.to_datetime(data_current['created_at'])
    return data_current

@router.post("/")
async def check_machine_status(data: dict):
    try:
        MONGO_URL = "mongodb://AMF_DB:W*123123*M@192.168.0.103:27021"
        MONGO_DB_NAME = "test"
        db = connect_mongo(MONGO_URL, MONGO_DB_NAME)

        num_days = int(data.get('num_days', 0))
        current_date = datetime.utcnow().date()

        response_data = []

        for day in range(num_days):
            current_date = current_date - timedelta(days=1)
            current_day_start = datetime.combine(current_date, datetime.min.time())
            current_day_end = current_day_start + timedelta(days=1)

            data_current = get_data_for_day(db, current_day_start, current_day_end)
            average_current = calculate_average_current(data_current)

            off_timestamps = data_current[(data_current[['CT1', 'CT2', 'CT3']] == 0).any(axis=1) | (average_current == 0)]['created_at']

            response_data.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "machine_status": "off" if not off_timestamps.empty else "on",
                "off_timestamps": off_timestamps.to_list()
            })

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
