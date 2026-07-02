import sqlite3
import os
import logging

logger = logging.getLogger("Database")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Define DB path in data/ directory relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(PROJECT_ROOT, 'data')
DB_PATH = os.path.join(DB_DIR, 'weather.db')

def get_db_connection():
    """
    Establish a connection to the SQLite database.
    Automatically ensures the directory exists.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize the database and create tables if they do not exist.
    """
    logger.info("Initializing SQLite database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create weather_forecast table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_forecast (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            forecast_time TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            rain_probability REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(location, forecast_time) ON CONFLICT REPLACE
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def save_forecasts(rows):
    """
    Save parsed weather forecast rows into the database.
    Each row in rows must be a dictionary with keys:
    location, forecast_time, temperature, humidity, rain_probability
    """
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
        INSERT INTO weather_forecast (
            location, forecast_time, temperature, humidity, rain_probability
        ) VALUES (?, ?, ?, ?, ?)
    '''
    
    insert_data = []
    for r in rows:
        insert_data.append((
            r.get('location'),
            r.get('forecast_time'),
            r.get('temperature'),
            r.get('humidity'),
            r.get('rain_probability')
        ))
        
    cursor.executemany(query, insert_data)
    conn.commit()
    inserted_count = cursor.rowcount
    conn.close()
    logger.info(f"Saved {len(rows)} forecast records into the database.")
    return len(rows)

if __name__ == '__main__':
    init_db()
