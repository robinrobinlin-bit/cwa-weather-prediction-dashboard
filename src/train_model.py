import sqlite3
import os
import sys
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import get_db_connection
from backend.models import insert_model_metrics

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
MODEL_PATH = os.path.join(MODELS_DIR, 'temperature_model.pkl')

def prepare_features(df):
    # Ensure forecast_time is datetime
    df['forecast_time_dt'] = pd.to_datetime(df['forecast_time'])
    df = df.sort_values(by=['location_name', 'forecast_time_dt'])
    
    # Fill missing values using forward fill and backward fill per location
    df['humidity'] = df.groupby('location_name')['humidity'].ffill().bfill()
    df['rain_probability'] = df.groupby('location_name')['rain_probability'].ffill().bfill()
    df['wind_speed'] = df.groupby('location_name')['wind_speed'].ffill().bfill()
    
    # Feature engineering: time features
    df['hour'] = df['forecast_time_dt'].dt.hour
    df['day_of_week'] = df['forecast_time_dt'].dt.dayofweek
    df['month'] = df['forecast_time_dt'].dt.month
    
    # Feature engineering: lag features
    df['previous_temperature'] = df.groupby('location_name')['temperature'].shift(1)
    
    # Feature engineering: rolling mean features
    # Min_periods=1 ensures we get values even if window isn't full
    df['rolling_mean_temperature'] = df.groupby('location_name')['temperature'].transform(
        lambda x: x.shift(1).rolling(window=3, min_periods=1).mean()
    )
    
    # Encode location_name as numeric category
    df['location_name'] = df['location_name'].astype('category')
    df['location_encoded'] = df['location_name'].cat.codes
    
    # Drop rows with NaN (which will be the first row of each location group due to shift)
    df = df.dropna(subset=['previous_temperature', 'rolling_mean_temperature', 'temperature'])
    
    return df

def train_and_save_model():
    print("Fetching training data from database...")
    conn = get_db_connection()
    try:
        # Load all weather forecast data
        df = pd.read_sql_query("SELECT * FROM weather_forecast", conn)
    except Exception as e:
        conn.close()
        return {"status": "error", "message": f"Could not load data: {e}"}
        
    if len(df) < 50:
        conn.close()
        return {
            "status": "error", 
            "message": f"Insufficient data for training. Only {len(df)} records found. Need at least 50."
        }
        
    print("Preprocessing data and engineering features...")
    # Prepare categories map
    df['location_name'] = df['location_name'].astype('category')
    location_categories = df['location_name'].cat.categories.tolist()
    
    df_prepared = prepare_features(df)
    
    if len(df_prepared) < 20:
        conn.close()
        return {"status": "error", "message": "Insufficient records after feature engineering."}
        
    # Define features and target
    feature_cols = [
        'hour', 'day_of_week', 'month', 'previous_temperature', 
        'humidity', 'rain_probability', 'wind_speed', 'location_encoded', 
        'rolling_mean_temperature'
    ]
    target_col = 'temperature'
    
    X = df_prepared[feature_cols]
    y = df_prepared[target_col]
    
    # Simple split: train on first 80%, test on last 20% (respecting time order)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    print("Training RandomForestRegressor model...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Predict and evaluate
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    
    print(f"Metrics - MAE: {mae:.2f}, RMSE: {rmse:.2f}, R2 Score: {r2:.2f}, MAPE: {mape:.2f}%")
    
    # Save model metrics to database
    print("Saving metrics to database...")
    insert_model_metrics(conn, "RandomForestRegressor", "temperature", mae, rmse, r2, mape)
    conn.close()
    
    # Save model and mapping to disk
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_data = {
        'model': model,
        'features': feature_cols,
        'location_categories': location_categories,
        'trained_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
        
    print(f"Model saved to {MODEL_PATH}")
    return {
        "status": "success",
        "message": "Model trained and saved successfully.",
        "metrics": {
            "model_name": "RandomForestRegressor",
            "mae": round(float(mae), 4),
            "rmse": round(float(rmse), 4),
            "r2_score": round(float(r2), 4),
            "mape": round(float(mape), 4)
        }
    }

if __name__ == '__main__':
    res = train_and_save_model()
    print(res)
