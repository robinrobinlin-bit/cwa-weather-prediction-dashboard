import sqlite3
import os
import sys
import pickle
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import get_db_connection
from backend.models import insert_predictions
from src.train_model import prepare_features, MODEL_PATH

def generate_predictions():
    if not os.path.exists(MODEL_PATH):
        return {"status": "error", "message": "Model file not found. Train the model first."}
        
    print("Loading model...")
    with open(MODEL_PATH, 'rb') as f:
        model_data = pickle.load(f)
        
    model = model_data['model']
    features = model_data['features']
    location_categories = model_data['location_categories']
    
    print("Fetching forecast data...")
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM weather_forecast", conn)
    except Exception as e:
        conn.close()
        return {"status": "error", "message": f"Could not read database: {e}"}
        
    if len(df) == 0:
        conn.close()
        return {"status": "error", "message": "No forecast data found to predict."}
        
    print("Preparing features...")
    # Map category to matching categorical type to make sure code numbers are exactly the same
    df['location_name'] = pd.Categorical(df['location_name'], categories=location_categories)
    
    df_prepared = prepare_features(df)
    
    if len(df_prepared) == 0:
        conn.close()
        return {"status": "error", "message": "No data left after feature engineering."}
        
    print("Running model inference...")
    X = df_prepared[features]
    predictions = model.predict(X)
    
    df_prepared['predicted_temperature'] = predictions
    
    # Calculate overall errors for this prediction run
    mae = float(np.mean(np.abs(df_prepared['temperature'] - predictions)))
    rmse = float(np.sqrt(np.mean((df_prepared['temperature'] - predictions)**2)))
    
    # Prepare rows for database insert
    prediction_rows = []
    for _, r in df_prepared.iterrows():
        prediction_rows.append({
            'location_name': str(r['location_name']),
            'prediction_time': str(r['forecast_time']),
            'predicted_temperature': round(float(r['predicted_temperature']), 2),
            'model_name': 'RandomForestRegressor',
            'mae': round(mae, 4),
            'rmse': round(rmse, 4)
        })
        
    print("Writing predictions to database...")
    # Clear old predictions to avoid duplicate keys
    cursor = conn.cursor()
    cursor.execute("DELETE FROM weather_prediction WHERE model_name = 'RandomForestRegressor'")
    conn.commit()
    
    inserted = insert_predictions(conn, prediction_rows)
    conn.close()
    
    print(f"Stored {inserted} AI predictions in SQLite.")
    return {
        "status": "success",
        "message": f"Successfully generated and saved {inserted} AI predictions.",
        "mae": mae,
        "rmse": rmse
    }

if __name__ == '__main__':
    res = generate_predictions()
    print(res)
