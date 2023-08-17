from fastapi import APIRouter, HTTPException, Body
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from .database import connect_mongo

router = APIRouter()


def calculate_productive_hours(data, scheduled_start_time, scheduled_end_time):
    # Your calculate_productive_hours function code here
    productive_data = data[data['average_current'] > 30]

    # Filter rows within the scheduled machine hours
    scheduled_data = productive_data[(productive_data['created_at'] >= scheduled_start_time) &
                                     (productive_data['created_at'] <= scheduled_end_time)]

    # Calculate productive machine hours
    if len(scheduled_data) > 0:
        productive_hours = (scheduled_data['created_at'].iloc[-1] - scheduled_data['created_at'].iloc[0]).total_seconds() / 3600
    else:
        productive_hours = 0

    return productive_hours

def plot_machine_utilization(scheduled_hours, productive_hours):
    # Your plot_machine_utilization function code here
    non_productive_hours = scheduled_hours - productive_hours

    # Create a pie chart for machine utilization
    labels = ['Productive Hours', 'Non-Productive Hours']
    sizes = [productive_hours, non_productive_hours]
    colors = ['green', 'red']
    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title("Machine Utilization")
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.show()

@router.post("/")
async def calculate_machine_utilization(data: dict = Body(...)):
    try:
        db = connect_mongo()
        
        mac_address = data.get('mac_address')
        if not mac_address:
            raise HTTPException(status_code=400, detail="Missing 'mac_address' in request data")
        
        node_document = db['nodes'].find_one({
            "mac": mac_address
        })
        phase = node_document['ct']['phase']

        scheduled_hours = int(data.get('scheduled_hours'))

        current_time = datetime.utcnow()
        start_time = current_time - timedelta(hours=scheduled_hours)

        cursor = db['cts'].find({
            "mac": mac_address,
            "created_at": {"$gte": start_time, "$lte": current_time}
        })

        data = pd.DataFrame(list(cursor))
        data['created_at'] = pd.to_datetime(data['created_at'])

        # Calculate average current for CT1, CT2, and CT3 for each hour
        if phase == 1:
            data['average_current'] = data['CT1']
        elif phase == 3:
            data['average_current'] = (data['CT1'] + data['CT2'] + data['CT3']) / 3
        else:
            raise ValueError("Invalid phase value. Supported values are 1 and 3.")

        data['average_current'] = data['average_current'].fillna(0)
        
        productive_hours = calculate_productive_hours(data, start_time, current_time)

        utilization = (productive_hours / scheduled_hours) * 100
        utilization = min(utilization, 100.0)  # Cap utilization at 100%

       # plot_machine_utilization(scheduled_hours, productive_hours)

        response_data = {
            "utilization": utilization,
            "productive_hours": productive_hours,
            "scheduled_hours": scheduled_hours
        }

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


""" Included pie chart """