import urllib.request
import json
import ssl
import csv
import sqlite3
import os

def to_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

def to_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def load_dotenv(dotenv_path=".env"):
    if os.path.exists(dotenv_path):
        try:
            with open(dotenv_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()
        except Exception as e:
            print(f"Warning: Could not read .env file: {e}")

def main():
    load_dotenv()
    auth_key = os.environ.get("CWA_AUTHORIZATION_KEY")
    if not auth_key:
        print("Error: CWA_AUTHORIZATION_KEY not found in environment or .env file.")
        return
        
    url = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-D0047-001?Authorization={auth_key}&downloadType=WEB&format=JSON"
    
    print("Downloading weather data from CWA...")
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            raw_data = response.read().decode('utf-8')
            data = json.loads(raw_data)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    print("Parsing weather data...")
    try:
        locations_list = data['cwaopendata']['Dataset']['Locations']['Location']
    except KeyError as e:
        print(f"Unexpected JSON structure: missing key {e}")
        return

    # Prepare rows for flattening
    rows = []
    
    # We will map fields based on the WeatherElement ElementName
    field_mappings = {
        '溫度': [('temperature', 'Temperature', to_int)],
        '露點溫度': [('dew_point', 'DewPoint', to_int)],
        '相對濕度': [('relative_humidity', 'RelativeHumidity', to_int)],
        '體感溫度': [('apparent_temperature', 'ApparentTemperature', to_int)],
        '舒適度指數': [
            ('comfort_index', 'ComfortIndex', to_int),
            ('comfort_index_desc', 'ComfortIndexDescription', str)
        ],
        '風速': [
            ('wind_speed', 'WindSpeed', to_int),
            ('wind_speed_beaufort', 'BeaufortScale', to_int)
        ],
        '風向': [('wind_direction', 'WindDirection', str)],
        '3小時降雨機率': [('rain_probability', 'ProbabilityOfPrecipitation', to_int)],
        '天氣現象': [
            ('weather', 'Weather', str),
            ('weather_code', 'WeatherCode', str)
        ],
        '天氣預報綜合描述': [('weather_description', 'WeatherDescription', str)]
    }

    for loc in locations_list:
        loc_name = loc['LocationName']
        geocode = loc['Geocode']
        lat = to_float(loc['Latitude'])
        lon = to_float(loc['Longitude'])

        # Store time-series data for this location
        # Keyed by time (DataTime or StartTime)
        loc_forecasts = {}

        for elem in loc.get('WeatherElement', []):
            elem_name = elem.get('ElementName')
            if elem_name not in field_mappings:
                continue
            
            mappings = field_mappings[elem_name]
            
            for time_entry in elem.get('Time', []):
                # Align on start_time
                time_key = time_entry.get('DataTime') or time_entry.get('StartTime')
                end_time_key = time_entry.get('EndTime')

                if not time_key:
                    continue

                if time_key not in loc_forecasts:
                    loc_forecasts[time_key] = {
                        'location_name': loc_name,
                        'geocode': geocode,
                        'latitude': lat,
                        'longitude': lon,
                        'time': time_key,
                        'end_time': end_time_key,
                        'temperature': None,
                        'dew_point': None,
                        'relative_humidity': None,
                        'apparent_temperature': None,
                        'comfort_index': None,
                        'comfort_index_desc': None,
                        'wind_speed': None,
                        'wind_speed_beaufort': None,
                        'wind_direction': None,
                        'rain_probability': None,
                        'weather': None,
                        'weather_code': None,
                        'weather_description': None
                    }
                
                # Update end_time if it exists in the time entry
                if end_time_key and not loc_forecasts[time_key]['end_time']:
                    loc_forecasts[time_key]['end_time'] = end_time_key

                # Parse element value
                elem_val = time_entry.get('ElementValue', {})
                for col_name, json_key, converter in mappings:
                    raw_val = elem_val.get(json_key)
                    if raw_val is not None:
                        loc_forecasts[time_key][col_name] = converter(raw_val)

        # Append all sorted forecasts for this location
        for time_key in sorted(loc_forecasts.keys()):
            rows.append(loc_forecasts[time_key])

    print(f"Total parsed records: {len(rows)}")

    # Define fields
    fields = [
        'location_name', 'geocode', 'latitude', 'longitude', 'time', 'end_time',
        'temperature', 'dew_point', 'relative_humidity', 'apparent_temperature',
        'comfort_index', 'comfort_index_desc', 'wind_speed', 'wind_speed_beaufort',
        'wind_direction', 'rain_probability', 'weather', 'weather_code', 'weather_description'
    ]

    # Save to CSV
    csv_file = 'weather_data.csv'
    print(f"Saving to CSV: {csv_file}...")
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print("CSV saved successfully.")
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return

    # Save to SQLite database
    db_file = 'weatherdb'
    db_file_sqlite = 'weatherdb.sqlite'
    print(f"Saving to SQLite database: {db_file}...")
    
    # Clean up existing database files if any to avoid appending duplicate data on rerun
    for df in [db_file, db_file_sqlite]:
        if os.path.exists(df):
            try:
                os.remove(df)
            except Exception as e:
                print(f"Warning: could not remove existing file {df}: {e}")

    try:
        # Create SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name TEXT,
                geocode TEXT,
                latitude REAL,
                longitude REAL,
                time TEXT,
                end_time TEXT,
                temperature INTEGER,
                dew_point INTEGER,
                relative_humidity INTEGER,
                apparent_temperature INTEGER,
                comfort_index INTEGER,
                comfort_index_desc TEXT,
                wind_speed INTEGER,
                wind_speed_beaufort INTEGER,
                wind_direction TEXT,
                rain_probability INTEGER,
                weather TEXT,
                weather_code TEXT,
                weather_description TEXT
            )
        ''')
        
        # Insert rows
        insert_query = f'''
            INSERT INTO weather_forecasts (
                {", ".join(fields)}
            ) VALUES ({", ".join(["?" for _ in fields])})
        '''
        
        insert_data = []
        for row in rows:
            insert_data.append(tuple(row[field] for field in fields))
            
        cursor.executemany(insert_query, insert_data)
        conn.commit()
        conn.close()
        
        print(f"Database '{db_file}' created and populated successfully.")
        
        # Also duplicate database as weatherdb.sqlite for standard clients
        import shutil
        shutil.copyfile(db_file, db_file_sqlite)
        print(f"Database copied to '{db_file_sqlite}' for standard compatibility.")
        
        # Also save to Excel
        excel_file = 'weather_data.xlsx'
        try:
            import pandas as pd
            df = pd.DataFrame(rows)
            # Reorder columns to match fields list
            df = df[fields]
            df.to_excel(excel_file, index=False, sheet_name='Weather Forecasts')
            print(f"Excel file '{excel_file}' created and populated successfully.")
        except Exception as ex_err:
            print(f"Warning: Could not save to Excel: {ex_err}")
        
    except Exception as e:
        print(f"Error saving to SQLite database: {e}")

if __name__ == '__main__':
    main()
