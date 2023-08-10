import os
from fastapi import FastAPI
from routers import fault_detection, bill_calculation, machine_utilization, max_consumption_day, monitor_power_usage, test_current_load_threshold, test_on_off_alert, two_days_comparison
from fastapi.openapi.models import Info

app = FastAPI()
port = int(os.environ.get("PORT", 8001))

app = FastAPI(
    title="My FastAPI App",
    description="This is a simple API built with FastAPI.",
    version="1.0.0",
    openapi_info=Info(
        title="My FastAPI App",
        description="This is a simple API built with FastAPI.",
        version="1.0.0"
    )
)

@app.get('/')
def home():
    return {"message": "Welcome to the app!"}

app.include_router(fault_detection.router, prefix='/fault-detection', tags=['fault-detection'])
app.include_router(bill_calculation.router, prefix='/bill-calculation', tags=['bill-calculation'])
app.include_router(machine_utilization.router, prefix='/machine-utilization', tags=['machine-utilization'])
app.include_router(max_consumption_day.router, prefix='/max-consumption-day', tags=['max-consumption-day'])
app.include_router(monitor_power_usage.router, prefix='/monitor-power-usage', tags=['monitor-power-usage'])
app.include_router(test_current_load_threshold.router, prefix='/test-current-load-threshold', tags=['test-current-load-threshold'])
app.include_router(test_on_off_alert.router, prefix='/test-on-off-alert', tags=['test-on-off-alert'])
app.include_router(two_days_comparison.router, prefix='/two-days-comparison', tags=['two-days-comparison'])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=port)
