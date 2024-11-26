from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import time

# Initialize the FastAPI app
app = FastAPI()

# In-memory storage for LDR data and alerts
ldr_data = []
alerts = []

# Data model for LDR sensor values
class LDRData(BaseModel):
    value: int
    timestamp: datetime

# Data model for alert logs
class Alert(BaseModel):
    timestamp: datetime
    duration: float  # in seconds

# Track the start time when the LDR value is below 1000
alert_start_time = None

# Store the LDR values in memory and return them
@app.post("/ldr-data/")
async def log_ldr_data(ldr: LDRData):
    global alert_start_time

    # Store the LDR data in memory
    ldr_data.append(ldr)

    # Check if the LDR value is below 1000 and track the alert start time
    if ldr.value < 1000:
        if alert_start_time is None:
            alert_start_time = time.time()  # Start the alert timer
    else:
        if alert_start_time is not None:
            # Calculate duration of the alert
            duration = time.time() - alert_start_time
            alerts.append(Alert(timestamp=datetime.now(), duration=duration))
            alert_start_time = None  # Reset the timer
    
    return {"message": "LDR data logged successfully."}

# Get the LDR data logged so far
@app.get("/ldr-data/")
async def get_ldr_data():
    return ldr_data

# Get all alert logs
@app.get("/alerts/")
async def get_alerts():
    return alerts

# Endpoint to perform calculations, e.g., time the LDR value was below 1000
@app.get("/calculations/")
async def get_alert_calculations():
    total_alert_time = sum([alert.duration for alert in alerts])
    alert_count = len(alerts)
    return {
        "total_alert_time_seconds": total_alert_time,
        "alert_count": alert_count,
        "average_alert_time_seconds": total_alert_time / alert_count if alert_count > 0 else 0
    }

# Health check endpoint to confirm the API is running
@app.get("/health/")
async def health_check():
    return {"status": "API is running"}

