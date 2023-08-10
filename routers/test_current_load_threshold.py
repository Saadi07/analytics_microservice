from fastapi import APIRouter, HTTPException, Body
from datetime import datetime, timedelta
import pandas as pd
from pymongo import MongoClient

router = APIRouter()

def calculate_power_usage(current_data, voltage, num_entries):
    # Your calculate_power_usage function code here
    power_usage = []
    for i, entry in enumerate(current_data):
        time = entry['created_at']
        current_phase1 = entry['CT1']
        current_phase2 = entry['CT2']
        current_phase3 = entry['CT3']
        power_phase1 = current_phase1 * voltage
        power_phase2 = current_phase2 * voltage
        power_phase3 = current_phase3 * voltage
        power_average = (power_phase1 + power_phase2 + power_phase3) / 3  # Calculate average power
        power_usage.append((time, power_average))
        if i + 1 >= num_entries:
            break
    return power_usage

def connect_mongo(url, db_name):
    client = MongoClient(url)
    db = client[db_name]
    return db

def get_historical_data(db, mac_address, start_time, end_time):
    cursor = db['cts'].find({
        "mac": mac_address,
        "created_at": {"$gte": start_time, "$lte": end_time}
    })

    data = pd.DataFrame(list(cursor))
    data['created_at'] = pd.to_datetime(data['created_at'])
    return data

@router.post("/")
async def perform_load_analysis(data: dict = Body(...)):
    try:
        MONGO_URL = "mongodb://AMF_DB:W*123123*M@192.168.0.103:27021"
        MONGO_DB_NAME = "test"
        db = connect_mongo(MONGO_URL, MONGO_DB_NAME)

        mac_address = data.get('mac_address')
        if not mac_address:
            raise HTTPException(status_code=400, detail="Please provide a valid MAC address.")

        hours = int(data.get('hours', 0))
        load_threshold = float(data.get('load_threshold', 0.0))

        duration = timedelta(hours=hours)
        end_time = datetime.utcnow()
        start_time = end_time - duration
        data = get_historical_data(db, mac_address, start_time, end_time)

        voltage = 220  # Voltage in Volts
        num_entries = hours * 60 * 60 // 5
        power_usage = calculate_power_usage(data.to_dict('records'), voltage, num_entries)

        exceed_threshold = [time for time, power in power_usage if power > load_threshold]
        alert_message = "Load threshold exceeded at the following times:" if exceed_threshold else "No load threshold exceeded."

        response_data = {
            "power_usage": power_usage,
            "alert": alert_message,
            "load_threshold_exceeded_times": exceed_threshold
        }

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
