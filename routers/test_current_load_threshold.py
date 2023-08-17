from fastapi import APIRouter, HTTPException, Body
from datetime import datetime, timedelta
import pandas as pd
from .database import connect_mongo

router = APIRouter()

def calculate_power_usage(current_data, voltage, num_entries, phase):
    power_usage = []
    for i, entry in enumerate(current_data):
        time = entry['created_at']
        
        if phase == 1:
            current_phase = entry['CT1']
        elif phase == 3:
            current_phase = (entry['CT1'] + entry['CT2'] + entry['CT3']) / 3
        else:
            raise ValueError("Invalid phase value. Supported values are 1 and 3.")
        
        power = current_phase * voltage
        power_usage.append((time, power))
        
        if i + 1 >= num_entries:
            break
    
    return power_usage

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
        db = connect_mongo()

        mac_address = data.get('mac_address')
        if not mac_address:
            raise HTTPException(status_code=400, detail="Please provide a valid MAC address.")
        
        node_document = db['nodes'].find_one({
            "mac": mac_address
        })
        phase = node_document['ct']['phase']
        
        hours = int(data.get('hours', 0))
        load_threshold = float(data.get('load_threshold', 0.0))

        duration = timedelta(hours=hours)
        end_time = datetime.utcnow()
        start_time = end_time - duration
        data = get_historical_data(db, mac_address, start_time, end_time)

        voltage = 220  # Voltage in Volts
        num_entries = hours * 60 * 60 // 5
        power_usage = calculate_power_usage(data.to_dict('records'), voltage, num_entries, phase)

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


""" Include line graph """