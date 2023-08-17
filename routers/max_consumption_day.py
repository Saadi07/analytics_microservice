from fastapi import APIRouter, HTTPException, Body
import pandas as pd
from datetime import datetime, timedelta
import numpy as np;
from .database import connect_mongo

router = APIRouter()

def calculate_average_power_consumed(data, voltage, phase):
    # Your calculate_average_power_consumed function code here
    if phase == 3:
        print("here")
        current_phase1 = data['CT1']
        current_phase2 = data['CT2']
        current_phase3 = data['CT3']
        power_phase1 = current_phase1 * voltage
        power_phase2 = current_phase2 * voltage
        power_phase3 = current_phase3 * voltage
        average_power = (power_phase1 + power_phase2 + power_phase3) / 3
        return average_power
    elif phase == 1:
        average_power_phase1 = np.mean(data['CT1']) * voltage
        return average_power_phase1
    else:
        raise ValueError("Invalid phase value. Supported values are 1 and 3.")
        

@router.post("/")
async def calculate_max_consumption_day(data: dict = Body(...)):
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

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        cursor = db['cts'].find({
            "mac": mac_address,
            "created_at": {"$gte": start_time, "$lte": end_time}
        })

        data = pd.DataFrame(list(cursor))
        data['created_at'] = pd.to_datetime(data['created_at'])

        voltage = 220  # Voltage in Volts
        data['power_consumed'] = calculate_average_power_consumed(data, voltage, phase)

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


""" Graph Include """