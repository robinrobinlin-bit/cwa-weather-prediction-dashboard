from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import get_db_connection
from backend.models import get_forecasts, get_predictions, get_latest_metrics, get_unique_locations
from src.cwa_client import fetch_and_save_weather_forecasts
from src.train_model import train_and_save_model
from src.predict import generate_predictions

app = FastAPI(title="CWA Weather & AI Prediction API", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "title": "CWA OpenData + Windy API + AI Forecast Backend",
        "docs_url": "/docs",
        "status": "online"
    }

@app.get("/api/cwa/fetch")
def fetch_cwa_data():
    """
    Fetch latest CWA weather forecast and save to database.
    """
    result = fetch_and_save_weather_forecasts()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/api/weather/locations")
def get_locations():
    """
    Get all unique weather station/township locations.
    """
    conn = get_db_connection()
    try:
        locs = get_unique_locations(conn)
        return {"locations": locs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/weather/forecast")
def get_forecast(location: str = Query(None, description="Location name, e.g. '宜蘭縣 宜蘭市'")):
    """
    Get weather forecasts, optionally filtered by location.
    """
    conn = get_db_connection()
    try:
        data = get_forecasts(conn, location)
        return {
            "location": location if location else "all",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/weather/predict")
def get_prediction(location: str = Query(None, description="Location name, e.g. '宜蘭縣 宜蘭市'")):
    """
    Get AI temperature predictions, optionally filtered by location.
    """
    conn = get_db_connection()
    try:
        predictions = get_predictions(conn, location)
        return {
            "location": location if location else "all",
            "model": "RandomForestRegressor",
            "predictions": predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/model/train")
def train_model_endpoint():
    """
    Trigger retraining of the AI model and update predictions.
    """
    train_result = train_and_save_model()
    if train_result["status"] == "error":
        raise HTTPException(status_code=500, detail=train_result["message"])
        
    predict_result = generate_predictions()
    if predict_result["status"] == "error":
        raise HTTPException(status_code=500, detail=predict_result["message"])
        
    return {
        "status": "success",
        "message": "Model retrained and predictions regenerated successfully.",
        "train_metrics": train_result["metrics"],
        "prediction_mae": predict_result["mae"],
        "prediction_rmse": predict_result["rmse"]
    }

@app.get("/api/model/metrics")
def get_metrics():
    """
    Get historical metrics for model evaluation.
    """
    conn = get_db_connection()
    try:
        metrics = get_latest_metrics(conn)
        if not metrics:
            return {
                "model_name": "RandomForestRegressor",
                "mae": None,
                "rmse": None,
                "r2_score": None,
                "mape": None,
                "trained_at": None
            }
        return metrics[0]  # Return the latest trained metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
