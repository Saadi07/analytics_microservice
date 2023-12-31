from fastapi import APIRouter, HTTPException, Body
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .database import connect_mongo


router = APIRouter()

def calculate_average_power(data, voltage, phase):
    if phase == 1:
        average_power_phase1 = np.mean(data['CT1']) * voltage
        return average_power_phase1
    elif phase == 3:
        average_power_phase1 = np.mean(data['CT1']) * voltage
        average_power_phase2 = np.mean(data['CT2']) * voltage
        average_power_phase3 = np.mean(data['CT3']) * voltage
        average_power = (average_power_phase1 + average_power_phase2 + average_power_phase3) / 3
        return average_power
    else:
        raise ValueError("Invalid phase value. Supported values are 1 and 3.")


def generate_alert(day, average_power, threshold):
    # Your generate_alert function code here
    if average_power > threshold:
        return True
    else:
        return False

def calculate_bill(units, unit_cost):
    # Your calculate_bill function code here
    total_cost = units * unit_cost
    return total_cost

@router.post("/")
async def calculate_power_analysis(data: dict = Body(...)):
    try:
        db = connect_mongo()
        mac_address = data.get('mac_address')
        if not mac_address:
            raise HTTPException(status_code=400, detail="Missing 'mac_address' in request data")
        
        node_document = db['nodes'].find_one({
        "mac": mac_address
        })
        phase = node_document['ct']['phase']
       
        days = int(data.get('days', 0))
        unit_cost = float(data.get('unit_cost', 0.0))
        threshold = float(data.get('threshold', 0.0))

        current_time = datetime.utcnow()
        start_time = current_time - timedelta(days=days)

        cursor = db['cts'].find({
            "mac": mac_address,
            "created_at": {"$gte": start_time, "$lte": current_time}
        })

        data = pd.DataFrame(list(cursor))
        data['created_at'] = pd.to_datetime(data['created_at'])

        voltage = 220  # Voltage in Volts
        total_units = 0
        power_analysis = []
        for day in range(days):
            day_start = start_time + timedelta(days=day)
            day_end = day_start + timedelta(days=1)
            daily_data = data[(data['created_at'] >= day_start) & (data['created_at'] < day_end)]
            average_power = calculate_average_power(daily_data, voltage, phase)  # Pass phase information
            power_in_kw = average_power / 1000
            units = power_in_kw
            total_units += units
            exceeds_threshold = generate_alert(day + 1, average_power, threshold)
            power_analysis.append({
                "day": day + 1,
                "average_power": average_power,
                "units_consumed": units,
                "exceeds_threshold": exceeds_threshold
            })

        total_cost = calculate_bill(total_units, unit_cost)

        response_data = {
            "power_analysis": power_analysis,
            "total_units_consumed": total_units,
            "total_calculated_bill": total_cost
        }

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
