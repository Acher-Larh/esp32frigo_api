from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List
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
    start_timestamp: datetime
    end_timestamp: datetime
    duration: float  # in seconds
    min_value: int
    avg_value: float

# Endpoint to log batch of LDR data
@app.post("/ldr-data/")
async def log_ldr_batch(readings: List[LDRData]):
    # Process batch of readings
    alerts_in_batch = process_ldr_batch(readings)
    
    # Extend main data storage
    ldr_data.extend(readings)
    
    # Add any new alerts
    if alerts_in_batch:
        alerts.extend(alerts_in_batch)
    
    return {
        "message": f"Logged {len(readings)} readings",
        "new_alerts": len(alerts_in_batch)
    }

def process_ldr_batch(readings: List[LDRData]):
    # Detection threshold for low light
    LOW_LIGHT_THRESHOLD = 1000
    
    # Batch alerts to return
    batch_alerts = []
    
    # Track current alert state
    current_alert = None
    
    # Process readings for alert detection
    for reading in readings:
        # Check if reading is below threshold
        if reading.value < LOW_LIGHT_THRESHOLD:
            # Start or continue an alert
            if current_alert is None:
                # Start a new alert
                current_alert = {
                    'start_timestamp': reading.timestamp,
                    'min_value': reading.value,
                    'values': [reading.value]
                }
        else:
            # Check if we were in an alert state
            if current_alert is not None:
                # End the current alert
                current_alert['end_timestamp'] = reading.timestamp
                current_alert['duration'] = (current_alert['end_timestamp'] - current_alert['start_timestamp']).total_seconds()
                current_alert['avg_value'] = sum(current_alert['values']) / len(current_alert['values'])
                current_alert['min_value'] = min(current_alert['values'])
                
                # Create Alert object and add to batch
                batch_alerts.append(Alert(
                    start_timestamp=current_alert['start_timestamp'],
                    end_timestamp=current_alert['end_timestamp'],
                    duration=current_alert['duration'],
                    min_value=current_alert['min_value'],
                    avg_value=current_alert['avg_value']
                ))
                
                # Reset current alert
                current_alert = None
    
    # Handle case where batch ends during an alert
    if current_alert is not None:
        # Use the last reading's timestamp
        current_alert['end_timestamp'] = readings[-1].timestamp
        current_alert['duration'] = (current_alert['end_timestamp'] - current_alert['start_timestamp']).total_seconds()
        current_alert['avg_value'] = sum(current_alert['values']) / len(current_alert['values'])
        current_alert['min_value'] = min(current_alert['values'])
        
        batch_alerts.append(Alert(
            start_timestamp=current_alert['start_timestamp'],
            end_timestamp=current_alert['end_timestamp'],
            duration=current_alert['duration'],
            min_value=current_alert['min_value'],
            avg_value=current_alert['avg_value']
        ))
    
    return batch_alerts

# Get the LDR data logged so far
@app.get("/ldr-data/")
async def get_ldr_data(skip: int = 0, limit: int = 100):
    return ldr_data[skip:skip+limit]

# Get all alert logs
@app.get("/alerts/")
async def get_alerts(skip: int = 0, limit: int = 100):
    return alerts[skip:skip+limit]

# Endpoint to perform calculations
@app.get("/calculations/")
async def get_alert_calculations():
    # Calculate statistics for alerts
    if not alerts:
        return {
            "total_alert_time_seconds": 0,
            "alert_count": 0,
            "average_alert_time_seconds": 0,
            "total_alerts_below_threshold": 0,
            "average_min_value_during_alerts": 0
        }
    
    total_alert_time = sum([alert.duration for alert in alerts])
    alert_count = len(alerts)
    
    return {
        "total_alert_time_seconds": total_alert_time,
        "alert_count": alert_count,
        "average_alert_time_seconds": total_alert_time / alert_count,
        "total_alerts_below_threshold": alert_count,
        "average_min_value_during_alerts": sum([alert.min_value for alert in alerts]) / alert_count
    }

# Health check endpoint
@app.get("/health/")
async def health_check():
    return {
        "status": "API is running",
        "total_readings": len(ldr_data),
        "total_alerts": len(alerts)
    }

# Optional: Clear all data endpoint (use with caution)
@app.delete("/clear-data/")
async def clear_all_data():
    global ldr_data, alerts
    ldr_data.clear()
    alerts.clear()
    return {"message": "All data has been cleared"}
