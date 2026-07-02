import os
import sys
import pickle
import pandas as pd
import numpy as np

# Add parent directory to path so src can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import get_db_connection
from src.train import prepare_features, MODEL_PATH

def predict_temperatures():
    """
    Load the trained model and generate predictions on CWA forecast data.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Model file models/weather_model.pkl not found. Please train the model first.")
        
    with open(MODEL_PATH, 'rb') as f:
        model_data = pickle.load(f)
        
    model = model_data['model']
    features = model_data['features']
    location_categories = model_data['location_categories']
    
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM weather_forecast", conn)
    except Exception as e:
        conn.close()
        raise RuntimeError(f"Database read failed: {e}")
    finally:
        conn.close()
        
    if len(df) == 0:
        raise ValueError("No weather forecast records found in database to run prediction.")
        
    # Map category to matching categorical type to keep index values consistent
    df['location'] = pd.Categorical(df['location'], categories=location_categories)
    
    df_prepared = prepare_features(df)
    
    if len(df_prepared) == 0:
        raise ValueError("No records left to predict after feature engineering.")
        
    # Run prediction
    X = df_prepared[features]
    predictions = model.predict(X)
    
    df_prepared['predicted_temperature'] = predictions
    
    # Calculate overall stats
    mae = float(np.mean(np.abs(df_prepared['temperature'] - predictions)))
    rmse = float(np.sqrt(np.mean((df_prepared['temperature'] - predictions)**2)))
    
    # Convert location back to string for serialization
    df_prepared['location'] = df_prepared['location'].astype(str)
    
    # Prepare details response list
    results = []
    for _, row in df_prepared.iterrows():
        results.append({
            'location': row['location'],
            'forecast_time': row['forecast_time'],
            'actual_temperature': float(row['temperature']),
            'predicted_temperature': round(float(row['predicted_temperature']), 2)
        })
        
    return {
        'mae': round(model_data['mae'], 4),
        'rmse': round(model_data['rmse'], 4),
        'r2': round(model_data['r2'], 4),
        'run_mae': round(mae, 4),
        'run_rmse': round(rmse, 4),
        'predictions': results
    }

if __name__ == '__main__':
    # Try training if not found, then run prediction
    if not os.path.exists(MODEL_PATH):
        from src.train import train_model
        print("Training model first...")
        train_model()
    res = predict_temperatures()
    print(f"Generated {len(res['predictions'])} predictions. Evaluation metrics: MAE: {res['mae']}, RMSE: {res['rmse']}, R2: {res['r2']}")
