import sqlite3

def insert_forecasts(conn, rows):
    cursor = conn.cursor()
    # rows is a list of dictionaries with keys:
    # location_name, county, district, forecast_time, temperature, min_temperature,
    # max_temperature, humidity, rain_probability, weather_description, wind_speed, wind_direction, source
    
    query = '''
        INSERT INTO weather_forecast (
            location_name, county, district, forecast_time, temperature, min_temperature,
            max_temperature, humidity, rain_probability, weather_description, wind_speed, wind_direction, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    insert_data = []
    for r in rows:
        insert_data.append((
            r.get('location_name'),
            r.get('county'),
            r.get('district'),
            r.get('forecast_time'),
            r.get('temperature'),
            r.get('min_temperature'),
            r.get('max_temperature'),
            r.get('humidity'),
            r.get('rain_probability'),
            r.get('weather_description'),
            r.get('wind_speed'),
            r.get('wind_direction'),
            r.get('source', 'CWA')
        ))
        
    cursor.executemany(query, insert_data)
    conn.commit()
    return len(rows)

def get_forecasts(conn, location_name=None):
    cursor = conn.cursor()
    if location_name:
        cursor.execute('''
            SELECT * FROM weather_forecast 
            WHERE location_name = ? 
            ORDER BY forecast_time ASC
        ''', (location_name,))
    else:
        cursor.execute('''
            SELECT * FROM weather_forecast 
            ORDER BY location_name, forecast_time ASC
        ''')
    return [dict(row) for row in cursor.fetchall()]

def get_unique_locations(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT location_name FROM weather_forecast ORDER BY location_name ASC')
    return [row[0] for row in cursor.fetchall()]

def insert_predictions(conn, rows):
    cursor = conn.cursor()
    # rows is a list of dictionaries with keys:
    # location_name, prediction_time, predicted_temperature, model_name, mae, rmse
    query = '''
        INSERT INTO weather_prediction (
            location_name, prediction_time, predicted_temperature, model_name, mae, rmse
        ) VALUES (?, ?, ?, ?, ?, ?)
    '''
    
    insert_data = []
    for r in rows:
        insert_data.append((
            r.get('location_name'),
            r.get('prediction_time'),
            r.get('predicted_temperature'),
            r.get('model_name'),
            r.get('mae'),
            r.get('rmse')
        ))
        
    cursor.executemany(query, insert_data)
    conn.commit()
    return len(rows)

def get_predictions(conn, location_name=None):
    cursor = conn.cursor()
    if location_name:
        cursor.execute('''
            SELECT * FROM weather_prediction 
            WHERE location_name = ? 
            ORDER BY prediction_time ASC
        ''', (location_name,))
    else:
        cursor.execute('''
            SELECT * FROM weather_prediction 
            ORDER BY location_name, prediction_time ASC
        ''')
    return [dict(row) for row in cursor.fetchall()]

def insert_model_metrics(conn, model_name, target_variable, mae, rmse, r2_score, mape=None):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO model_metrics (
            model_name, target_variable, mae, rmse, r2_score, mape
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (model_name, target_variable, mae, rmse, r2_score, mape))
    conn.commit()
    return cursor.lastrowid

def get_latest_metrics(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM model_metrics 
        ORDER BY trained_at DESC 
        LIMIT 10
    ''')
    return [dict(row) for row in cursor.fetchall()]
