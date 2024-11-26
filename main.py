from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ValidationError
from datetime import datetime
from typing import List

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
    try:
        # Debug: Print the received payload
        print("Received readings:", readings)
        
        # Validate and process the batch of readings
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
    except ValidationError as e:
        print("Validation error:", e)
        raise HTTPException(status_code=400, detail="Invalid data format. Check 'value' and 'timestamp'.")
    except Exception as e:
        print("Unexpected error:", e)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# Function to process batch of readings (unchanged)
def process_ldr_batch(readings: List[LDRData]):
    LOW_LIGHT_THRESHOLD = 1000
    batch_alerts = []
    current_alert = None
    
    for reading in readings:
        if reading.value < LOW_LIGHT_THRESHOLD:
            if current_alert is None:
                current_alert = {
                    'start_timestamp': reading.timestamp,
                    'min_value': reading.value,
                    'values': [reading.value]
                }
        else:
            if current_alert is not None:
                current_alert['end_timestamp'] = reading.timestamp
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
                current_alert = None
    
    if current_alert is not None:
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

# Add a route to inspect received data for debugging
@app.get("/debug/")
async def debug_data():
    return {
        "ldr_data_sample": ldr_data[:5],
        "total_readings": len(ldr_data),
        "alerts_sample": alerts[:5],
        "total_alerts": len(alerts)
    }
