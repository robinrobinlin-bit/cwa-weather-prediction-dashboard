import urllib.request
import json
import ssl
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import get_db_connection
from backend.models import insert_forecasts

def load_dotenv(dotenv_path=".env"):
    # Load dotenv relative to the project root
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_dotenv_path = os.path.join(root_dir, dotenv_path)
    if os.path.exists(full_dotenv_path):
        try:
            with open(full_dotenv_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()
        except Exception as e:
            print(f"Warning: Could not read .env file: {e}")

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

def fetch_and_save_weather_forecasts():
    load_dotenv()
    
    # Check both CWA_API_KEY and CWA_AUTHORIZATION_KEY as per the design document guidelines
    auth_key = os.environ.get("CWA_API_KEY") or os.environ.get("CWA_AUTHORIZATION_KEY")
    if not auth_key:
        return {
            "status": "error",
            "message": "CWA_API_KEY or CWA_AUTHORIZATION_KEY not found in environment or .env file."
        }
        
    url = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-D0047-001?Authorization={auth_key}&downloadType=WEB&format=JSON"
    
    print("Downloading weather data from CWA...")
    ctx = ssl._create_unverified_context()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            raw_data = response.read().decode('utf-8')
            data = json.loads(raw_data)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching CWA API: {e}"
        }

    print("Parsing weather data...")
    try:
        locations_container = data['cwaopendata']['Dataset']['Locations']
        county = locations_container['LocationsName']
        locations_list = locations_container['Location']
    except KeyError as e:
        return {
            "status": "error",
            "message": f"Unexpected JSON structure: missing key {e}"
        }

    # Prepare rows for database
    rows = []
    
    # We will map fields based on the WeatherElement ElementName
    field_mappings = {
        '溫度': [('temperature', 'Temperature', to_float)],
        '相對濕度': [('humidity', 'RelativeHumidity', to_float)],
        '風速': [('wind_speed', 'WindSpeed', to_float)],
        '風向': [('wind_direction', 'WindDirection', str)],
        '3小時降雨機率': [('rain_probability', 'ProbabilityOfPrecipitation', to_float)],
        '天氣預報綜合描述': [('weather_description', 'WeatherDescription', str)]
    }

    for loc in locations_list:
        district = loc['LocationName']
        loc_name = f"{county} {district}"
        
        # Store time-series data for this location
        loc_forecasts = {}

        for elem in loc.get('WeatherElement', []):
            elem_name = elem.get('ElementName')
            if elem_name not in field_mappings:
                continue
            
            mappings = field_mappings[elem_name]
            
            for time_entry in elem.get('Time', []):
                time_key = time_entry.get('DataTime') or time_entry.get('StartTime')
                if not time_key:
                    continue

                # Standardize time format to YYYY-MM-DD HH:MM:SS
                try:
                    # ISO 8601 parsing
                    dt = datetime.strptime(time_key[:19], "%Y-%m-%dT%H:%M:%S")
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    formatted_time = time_key

                if formatted_time not in loc_forecasts:
                    loc_forecasts[formatted_time] = {
                        'location_name': loc_name,
                        'county': county,
                        'district': district,
                        'forecast_time': formatted_time,
                        'temperature': None,
                        'min_temperature': None,
                        'max_temperature': None,
                        'humidity': None,
                        'rain_probability': None,
                        'weather_description': None,
                        'wind_speed': None,
                        'wind_direction': None,
                        'source': 'CWA'
                    }
                
                # Parse element value
                elem_val = time_entry.get('ElementValue', {})
                for col_name, json_key, converter in mappings:
                    raw_val = elem_val.get(json_key)
                    if raw_val is not None:
                        loc_forecasts[formatted_time][col_name] = converter(raw_val)

        # Append all forecasts for this location
        for time_key in loc_forecasts:
            rows.append(loc_forecasts[time_key])

    print(f"Total parsed rows: {len(rows)}")
    
    # Save to database
    try:
        conn = get_db_connection()
        inserted = insert_forecasts(conn, rows)
        conn.close()
        return {
            "status": "success",
            "message": f"Successfully fetched and stored {inserted} forecast records."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database error during insert: {e}"
        }

if __name__ == '__main__':
    res = fetch_and_save_weather_forecasts()
    print(res)
