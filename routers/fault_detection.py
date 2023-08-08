from fastapi import APIRouter, HTTPException, Body
from pymongo import MongoClient
from datetime import datetime, timedelta
import time

router = APIRouter()

def connect_mongo(url, db_name):
    try:
        client = MongoClient(url)
        db = client[db_name]
        return db
    except Exception as e:
        raise RuntimeError(f"Error connecting to MongoDB: {e}")


def calculate_average(current_data):
    # Your calculate_average function code here
    ct1_sum = 0.0
    ct2_sum = 0.0
    ct3_sum = 0.0
    num_entries = len(current_data)

    for entry in current_data:
        ct1_sum += entry['CT1']
        ct2_sum += entry['CT2']
        ct3_sum += entry['CT3']

    average_ct1 = ct1_sum / num_entries
    average_ct2 = ct2_sum / num_entries
    average_ct3 = ct3_sum / num_entries

    return (average_ct1, average_ct2, average_ct3)
    pass

def detect_fault(average_current, fault_threshold):
    # Your detect_fault function code here
    timestamp = datetime.utcnow()
    if average_current > fault_threshold:
        return True, timestamp
    return False, None

@router.post("/")
async def start_fault_detection(data: dict):
    try:
        MONGO_URL = "mongodb://AMF_DB:W*123123*M@192.168.0.103:27021"
        MONGO_DB_NAME = "test"

        db = connect_mongo(MONGO_URL, MONGO_DB_NAME)

        fault_threshold = data.get('fault_threshold')
        cursor = db['cts'].find({
                    "mac": "70:b3:d5:fe:4d:09",
                    "created_at": {"$gte": datetime.utcnow() - timedelta(seconds=5)}
                })

        current_data = list(cursor)

        average_ct1, average_ct2, average_ct3 = calculate_average(current_data)

        average_current = (average_ct1 + average_ct2 + average_ct3) / 3

        is_fault, timestamp = detect_fault(average_current, fault_threshold)
        if is_fault:
            response = {
                        "results": f"Fault detected at {timestamp}: Average Current: {average_current} Amps"
                    }
            return response
        else:
            response = {
                        "results": f"No Fault Detected!"
                    }
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))