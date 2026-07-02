import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DB_PATH = os.path.join(DB_DIR, 'weather.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Ensure data directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Table: weather_forecast
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_forecast (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL,
            county TEXT,
            district TEXT,
            forecast_time DATETIME NOT NULL,
            temperature REAL,
            min_temperature REAL,
            max_temperature REAL,
            humidity REAL,
            rain_probability REAL,
            weather_description TEXT,
            wind_speed REAL,
            wind_direction TEXT,
            source TEXT DEFAULT 'CWA',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(location_name, forecast_time) ON CONFLICT REPLACE
        )
    ''')
    
    # 2. Table: weather_prediction
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_prediction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT NOT NULL,
            prediction_time DATETIME NOT NULL,
            predicted_temperature REAL,
            model_name TEXT,
            mae REAL,
            rmse REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(location_name, prediction_time, model_name) ON CONFLICT REPLACE
        )
    ''')
    
    # 3. Table: model_metrics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            target_variable TEXT,
            mae REAL,
            rmse REAL,
            r2_score REAL,
            mape REAL,
            trained_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
