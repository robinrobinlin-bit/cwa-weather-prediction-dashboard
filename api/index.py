from fastapi import FastAPI, HTTPException, Query
import sys
import os

# Add project root to python path so src can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.cwa_client import CWAClient
from src.database import save_forecasts
from src.predict import predict_temperatures

app = FastAPI(
    title="CWA Weather Prediction API",
    description="FastAPI Backend for Taiwan Weather Prediction and Windy Visualization Dashboard.",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Welcome to the CWA Weather Prediction API skeleton. Use /docs to view the API documentation."
    }

@app.get("/api/weather")
def get_weather(dataset_id: str = Query("F-D0047-001", description="CWA Dataset ID")):
    """
    Get the latest weather forecast from CWA OpenData.
    """
    client = CWAClient()
    try:
        data = client.get_forecast(dataset_id=dataset_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch forecast from CWA: {e}")

@app.post("/api/weather/update")
def update_weather(dataset_id: str = Query("F-D0047-001", description="CWA Dataset ID")):
    """
    Fetch forecasts from CWA and save parsed records to the SQLite database.
    """
    client = CWAClient()
    try:
        raw_data = client.get_forecast(dataset_id=dataset_id)
        parsed_rows = client.parse_forecast(raw_data)
        saved_count = save_forecasts(parsed_rows)
        return {
            "status": "success",
            "message": f"Successfully fetched and saved {saved_count} forecast records to the database."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update weather: {e}")

@app.get("/api/predict")
def get_predictions():
    """
    Run model predictions and return the forecasts alongside performance metrics.
    """
    try:
        results = predict_temperatures()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run predictions: {e}")
