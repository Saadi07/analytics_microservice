from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from pymongo import MongoClient
import pandas as pd
from .database import connect_mongo

router = APIRouter()

def calculate_power_consumed(data, voltage, phase):
    if phase == 1:
        power_phase = data['CT1'] * voltage
    elif phase == 3:
        power_phase = (data['CT1'] + data['CT2'] + data['CT3']) * voltage
    else:
        raise ValueError("Invalid phase value. Supported values are 1 and 3.")
    
    total_power = power_phase
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
        db = connect_mongo()

        mac_address = data.get('mac_address')
        if not mac_address:
            raise HTTPException(status_code=400, detail="Please provide a valid MAC address.")
        
        node_document = db['nodes'].find_one({
                "mac": mac_address
            })
        phase = node_document['ct']['phase']

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
        average_power_current = calculate_power_consumed(data_current, voltage, phase) * 1
        average_power_previous = calculate_power_consumed(data_previous, voltage, phase) * 1

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


""" Realtime data for the current day also Include graph """