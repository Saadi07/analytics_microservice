from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from datetime import datetime, timedelta
from .database import connect_mongo
import asyncio

router = APIRouter()

def calculate_power_usage(data, voltage, phase):
    if phase == 1:
        current_values = [entry['CT1'] for entry in data]
    elif phase == 3:
        current_values = [(entry['CT1'] + entry['CT2'] + entry['CT3']) / 3 for entry in data]
    else:
        raise ValueError("Invalid phase value. Supported values are 1 and 3.")
    
    average_current = sum(current_values) / len(current_values)
    power_usage = average_current * voltage
    return power_usage

async def send_realtime_power_usage(websocket: WebSocket, mac_address: str):
    try:
        db = connect_mongo()

        if not mac_address:
            raise HTTPException(status_code=400, detail="Please provide a valid MAC address.")
        
        node_document = db['nodes'].find_one({
            "mac": mac_address
        })
        phase = node_document['ct']['phase']

        voltage = 220  # Voltage in Volts

        while True:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(seconds=5)
            cursor = db['cts'].find({
                "mac": mac_address,
                "created_at": {"$gte": start_time, "$lt": end_time}
            })
            cursor_list = list(cursor)

            if len(cursor_list) > 0:
                power_usage = calculate_power_usage(cursor_list, voltage, phase)

                response_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "average_current": float(power_usage / voltage),
                    "power_usage": float(power_usage)
                }

                await websocket.send_json(response_data)

            else:
                await websocket.send_json({
                    "error": "No data available."
                })

            await asyncio.sleep(5)  # Send data every 5 seconds

    except WebSocketDisconnect:
        print("WebSocket disconnected.")
    except Exception as e:
        await websocket.send_json({
            "error": str(e)
        })

@router.websocket("/ws/realtime-power-usage/{mac_address}")
async def websocket_realtime_power_usage(websocket: WebSocket, mac_address: str):
    await websocket.accept()
    await send_realtime_power_usage(websocket, mac_address)



""" REaltime data and Graph Included """