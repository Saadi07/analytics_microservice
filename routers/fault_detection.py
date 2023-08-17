from fastapi import APIRouter, HTTPException, Body
from pymongo import MongoClient
from datetime import datetime, timedelta
from .database import connect_mongo

router = APIRouter()

def calculate_average(current_data, phase):
    ct_sum = 0.0
    num_entries = len(current_data)

    if phase == 1:
        for entry in current_data:
            ct_sum += entry['CT1']
        average_ct = ct_sum / num_entries
    elif phase == 3:
        ct1_sum = 0.0
        ct2_sum = 0.0
        ct3_sum = 0.0
        for entry in current_data:
            ct1_sum += entry['CT1']
            ct2_sum += entry['CT2']
            ct3_sum += entry['CT3']
        average_ct1 = ct1_sum / num_entries
        average_ct2 = ct2_sum / num_entries
        average_ct3 = ct3_sum / num_entries
        average_ct = (average_ct1 + average_ct2 + average_ct3) / 3
    else:
        raise ValueError("Invalid phase value. Supported values are 1 and 3.")

    return average_ct

def detect_fault(average_current, fault_threshold):
    # Your detect_fault function code here
    timestamp = datetime.utcnow()
    if average_current > fault_threshold:
        return True, timestamp
    return False, None

@router.post("/")
async def start_fault_detection(data: dict = Body(...)):
    try:
        db = connect_mongo()
        
        mac_address = data.get('mac_address')
        if not mac_address:
            raise HTTPException(status_code=400, detail="Missing 'mac_address' in request data")
        
        node_document = db['nodes'].find_one({
            "mac": mac_address
        })
        phase = node_document['ct']['phase']

        fault_threshold = data.get('fault_threshold')
        
        cursor = db['cts'].find({
            "mac": mac_address,
            "created_at": {"$gte": datetime.utcnow() - timedelta(seconds=5)}
        })

        current_data = list(cursor)

        average_current = calculate_average(current_data, phase)  # Using the calculated phase

        is_fault, timestamp = detect_fault(average_current, fault_threshold)
        if is_fault:
            response = {
                "results": f"Fault detected at {timestamp}: Average Current: {average_current} Amps"
            }
            return response
        else:
            response = {
                "results": "No Fault Detected!"
            }
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


""" Realtime data  """
