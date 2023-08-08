from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from datetime import datetime, timedelta

router = APIRouter()

def connect_mongo(url, db_name):
    client = MongoClient(url)
    db = client[db_name]
    return db

def calculate_power_usage(data, voltage):
    # Your calculate_power_usage function code here
    current_values = [data['CT1'] for data in data] + [data['CT2'] for data in data] + [data['CT3'] for data in data]
    average_current = sum(current_values) / len(current_values)
    power_usage = average_current * voltage
    return power_usage
    pass

@router.get("/")
async def realtime_power_usage():
    try:
        MONGO_URL = "mongodb://AMF_DB:W*123123*M@192.168.0.103:27021"
        MONGO_DB_NAME = "test"
        db = connect_mongo(MONGO_URL, MONGO_DB_NAME)

        voltage = 220  # Voltage in Volts

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(seconds=5)
        cursor = db['cts'].find({
            "mac": "70:b3:d5:fe:4d:09",
            "created_at": {"$gte": start_time, "$lt": end_time}
        })
        cursor_list = list(cursor)

        if len(cursor_list) > 0:
            power_usage = calculate_power_usage(cursor_list, voltage)

            response_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "average_current": float(power_usage / voltage),
                "power_usage": float(power_usage)
            }

            return response_data

        else:
            raise HTTPException(status_code=404, detail="No data available.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
