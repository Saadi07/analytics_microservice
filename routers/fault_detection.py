from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from datetime import datetime, timedelta
import json
import asyncio
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

@router.websocket("/ws/fault-detection")
async def start_fault_detection(websocket: WebSocket):
    await websocket.accept()
    db = connect_mongo()
    try:
        # Receive initial data from the client
        data = await websocket.receive_text()
        data = json.loads(data)
        mac_address = data.get('mac_address')
        fault_threshold = data.get('fault_threshold')

        if not mac_address:
            raise HTTPException(status_code=400, detail="Missing 'mac_address' in request data")
        
        node_document = db['nodes'].find_one({
            "mac": mac_address
        })
        phase = node_document['ct']['phase']

        while True:
            cursor = db['cts'].find({
                "mac": mac_address,
                "created_at": {"$gte": datetime.utcnow() - timedelta(seconds=5)}
            })

            current_data = list(cursor)

            average_current = calculate_average(current_data, phase)

            is_fault, timestamp = detect_fault(average_current, fault_threshold)
            if is_fault:
                response = {
                    "results": f"Fault detected at {timestamp}: Average Current: {average_current} Amps"
                }
            else:
                response = {
                    "results": "No Fault Detected!"
                }

            await websocket.send_json(response)

            await asyncio.sleep(5)  # Send data every 5 seconds

    except WebSocketDisconnect:
        print("Disconnected!")


""" Realtime data  """
