from fastapi import APIRouter, HTTPException
from fastapi.openapi.models import Info
from datetime import datetime, timedelta
from pymongo import MongoClient
import pandas as pd
from .database import connect_mongo

router = APIRouter()

def calculate_average_current(data, phase):
    if data.empty:
        return None
    
    if phase == 1:
        average_current = data['CT1']
    elif phase == 3:
        average_current = data[['CT1', 'CT2', 'CT3']].mean(axis=1)
    else:
        raise ValueError("Invalid phase value. Supported values are 1 and 3.")
    
    return average_current


def get_data_for_day(db, mac_address, current_day_start, current_day_end):
    cursor_current = db['cts'].find({
        "mac": mac_address,
        "created_at": {"$gte": current_day_start, "$lt": current_day_end}
    })

    data_current = pd.DataFrame(list(cursor_current))
    data_current['created_at'] = pd.to_datetime(data_current['created_at'])
    return data_current

@router.post("/")
async def check_machine_status(data: dict):
    try:
        db = connect_mongo()

        mac_address = data.get('mac_address')
        if not mac_address:
            raise HTTPException(status_code=400, detail="Please provide a valid MAC address.")

        mac_address = data.get('mac_address')
        if not mac_address:
            raise HTTPException(status_code=400, detail="Please provide a valid MAC address.")

        num_days = int(data.get('num_days', 0))
        current_date = datetime.utcnow().date()

        response_data = []

        for day in range(num_days):
            current_date = current_date - timedelta(days=1)
            current_day_start = datetime.combine(current_date, datetime.min.time())
            current_day_end = current_day_start + timedelta(days=1)

            data_current = get_data_for_day(db, mac_address, current_day_start, current_day_end)

            node_document = db['nodes'].find_one({
                "mac": mac_address
            })
            phase = node_document['ct']['phase']

            average_current = calculate_average_current(data_current, phase)

            off_timestamps = data_current[(data_current[['CT1', 'CT2', 'CT3']] == 0).any(axis=1) | (average_current == 0)]['created_at']

            response_data.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "machine_status": "off" if not off_timestamps.empty else "on",
                "off_timestamps": off_timestamps.to_list()
            })

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
