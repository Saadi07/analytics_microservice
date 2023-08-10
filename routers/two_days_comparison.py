from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from pymongo import MongoClient
import pandas as pd

router = APIRouter()

def connect_mongo(url, db_name):
    client = MongoClient(url)
    db = client[db_name]
    return db

def calculate_power_consumed(data, voltage):
    power_phase1 = data['CT1'] * voltage
    power_phase2 = data['CT2'] * voltage
    power_phase3 = data['CT3'] * voltage
    total_power = power_phase1 + power_phase2 + power_phase3
    average_power = total_power.mean()
    return average_power

def generate_alert(current_day_power, previous_day_power):
    if current_day_power > previous_day_power:
        return "Average power for the current day is greater than the previous day."
    elif current_day_power < previous_day_power:
        return "Average power for the current day is less than the previous day."
    else:
        return "Average power for the current day is equal to the previous day."

@router.post("/")
async def perform_load_analysis(data: dict):
    try:
        MONGO_URL = "mongodb://AMF_DB:W*123123*M@192.168.0.103:27021"
        MONGO_DB_NAME = "test"
        db = connect_mongo(MONGO_URL, MONGO_DB_NAME)

        mac_address = data.get('mac_address')
        if not mac_address:
            raise HTTPException(status_code=400, detail="Please provide a valid MAC address.")

        current_day = datetime.utcnow().date()
        previous_day = current_day - timedelta(days=1)

        current_day_start = datetime.combine(current_day, datetime.min.time())
        current_day_end = datetime.utcnow()
        previous_day_start = datetime.combine(previous_day, datetime.min.time())
        previous_day_end = previous_day_start + timedelta(days=1)

        cursor_current = db['cts'].find({
            "mac": mac_address,
            "created_at": {"$gte": current_day_start, "$lt": current_day_end}
        })
        cursor_previous = db['cts'].find({
            "mac": mac_address,
            "created_at": {"$gte": previous_day_start, "$lt": previous_day_end}
        })

        data_current = pd.DataFrame(list(cursor_current))
        data_previous = pd.DataFrame(list(cursor_previous))

        data_current['created_at'] = pd.to_datetime(data_current['created_at'])
        data_previous['created_at'] = pd.to_datetime(data_previous['created_at'])

        voltage = 220
        average_power_current = calculate_power_consumed(data_current, voltage) * 1
        average_power_previous = calculate_power_consumed(data_previous, voltage) * 1

        duration_current = ((current_day_end - current_day_start).total_seconds()) / 3600
        duration_previous = ((previous_day_end - previous_day_start).total_seconds()) / 3600

        units_current = (average_power_current * duration_current) / 1000
        units_previous = (average_power_previous * duration_previous) / 1000

        power_difference = average_power_current - average_power_previous
        units_difference = units_current - units_previous

        alert_message = generate_alert(average_power_current, average_power_previous)

        response_data = {
            "average_power_current": average_power_current,
            "average_power_previous": average_power_previous,
            "units_current": units_current,
            "units_previous": units_previous,
            "power_difference": power_difference,
            "units_difference": units_difference,
            "alert_message": alert_message,
        }

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
