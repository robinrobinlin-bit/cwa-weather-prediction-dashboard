import sqlite3
import os
import sys
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Add parent directory to path so src can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database import get_db_connection

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'weather_model.pkl')

def prepare_features(df):
    """
    Perform feature engineering: time components, lags, and rolling averages.
    """
    df['forecast_time_dt'] = pd.to_datetime(df['forecast_time'])
    df = df.sort_values(by=['location', 'forecast_time_dt'])
    
    # Fill gaps (e.g., rain probability is 3-hourly, temperature is hourly)
    df['humidity'] = df.groupby('location')['humidity'].ffill().bfill()
    df['rain_probability'] = df.groupby('location')['rain_probability'].ffill().bfill()
    
    # Time features
    df['hour'] = df['forecast_time_dt'].dt.hour
    df['day_of_week'] = df['forecast_time_dt'].dt.dayofweek
    df['month'] = df['forecast_time_dt'].dt.month
    
    # Lags and Rolling averages
    df['previous_temperature'] = df.groupby('location')['temperature'].shift(1)
    df['rolling_mean_temperature'] = df.groupby('location')['temperature'].transform(
        lambda x: x.shift(1).rolling(window=3, min_periods=1).mean()
    )
    
    # Encode location_name dynamically as categorical codes
    df['location'] = df['location'].astype('category')
    df['location_encoded'] = df['location'].cat.codes
    
    # Drop first entries where lags are NaN
    df = df.dropna(subset=['previous_temperature', 'rolling_mean_temperature', 'temperature'])
    return df

def train_model():
    """
    Train a RandomForestRegressor on CWA data and save model artifact.
    """
    os.makedirs(MODEL_DIR, exist_ok=True)
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM weather_forecast", conn)
    except Exception as e:
        conn.close()
        raise RuntimeError(f"Database read failed: {e}")
    finally:
        conn.close()

    if len(df) < 30:
        raise ValueError(f"Insufficient forecast records for training. Found {len(df)}. Need at least 30.")

    # Save categories order
    df['location'] = df['location'].astype('category')
    location_categories = df['location'].cat.categories.tolist()

    df_prepared = prepare_features(df)
    
    feature_cols = [
        'hour', 'day_of_week', 'month', 'previous_temperature', 
        'humidity', 'rain_probability', 'location_encoded', 
        'rolling_mean_temperature'
    ]
    target_col = 'temperature'
    
    X = df_prepared[feature_cols]
    y = df_prepared[target_col]
    
    # Chronological Split: 80% train, 20% test
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    # Model Training
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluation
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))
    r2 = r2_score(y_test, predictions)
    
    model_data = {
        'model': model,
        'features': feature_cols,
        'location_categories': location_categories,
        'mae': float(mae),
        'rmse': float(rmse),
        'r2': float(r2)
    }
    
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model_data, f)
        
    return model_data

if __name__ == '__main__':
    res = train_model()
    print(f"Model trained. MAE: {res['mae']:.4f}, RMSE: {res['rmse']:.4f}, R2: {res['r2']:.4f}")
