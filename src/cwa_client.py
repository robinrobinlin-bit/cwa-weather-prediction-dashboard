import os
import requests
import logging

# Configure logger
logger = logging.getLogger("CWAClient")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def load_dotenv(dotenv_path=".env"):
    """
    Simple utility to load environment variables from a local .env file.
    """
    # Look for .env relative to the project root directory
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
            logger.info("Successfully loaded environment variables from .env")
        except Exception as e:
            logger.error(f"Failed to read .env file: {e}")

class CWAClient:
    """
    Client for fetching weather forecast data from the Central Weather Administration (CWA) OpenData API.
    """
    def __init__(self, api_key=None):
        load_dotenv()
        self.api_key = api_key or os.environ.get("CWA_API_KEY")
        if not self.api_key:
            logger.warning("CWA_API_KEY is not set in environment variables or .env file.")
            
        self.base_url = "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi"

    def get_forecast(self, dataset_id="F-D0047-001"):
        """
        Fetch forecast data for a given dataset ID (default: F-D0047-001 for Yilan County).
        Returns the parsed JSON dictionary.
        """
        if not self.api_key:
            logger.error("Request failed: CWA_API_KEY is missing.")
            raise ValueError("CWA_API_KEY is not configured.")

        url = f"{self.base_url}/{dataset_id}"
        params = {
            "Authorization": self.api_key,
            "downloadType": "WEB",
            "format": "JSON"
        }

        logger.info(f"Sending request to CWA API for dataset {dataset_id}...")
        try:
            # Bypass SSL verification if local SSL certificate bundles are missing
            response = requests.get(url, params=params, verify=False, timeout=15)
            response.raise_for_status()
            
            logger.info("API request completed successfully.")
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - Response: {response.text}")
            raise RuntimeError(f"CWA API returned HTTP error: {http_err}") from http_err
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Network or request error occurred: {req_err}")
            raise RuntimeError(f"CWA API network/request error: {req_err}") from req_err
        except Exception as err:
            logger.error(f"An unexpected error occurred during API call: {err}")
            raise

    def parse_forecast(self, raw_data):
        """
        Parse raw CWA JSON forecast data into a list of standardized dicts.
        """
        from datetime import datetime
        
        try:
            locations_container = raw_data['cwaopendata']['Dataset']['Locations']
            county = locations_container['LocationsName']
            locations_list = locations_container['Location']
        except KeyError as e:
            logger.error(f"Failed to parse JSON: missing expected key {e}")
            raise ValueError(f"Invalid forecast JSON format: missing {e}")

        parsed_rows = []
        
        # We will parse Temperature, Relative Humidity, and Precipitation Probability
        element_mappings = {
            '溫度': 'temperature',
            '相對濕度': 'humidity',
            '3小時降雨機率': 'rain_probability'
        }
        
        element_keys = {
            '溫度': 'Temperature',
            '相對濕度': 'RelativeHumidity',
            '3小時降雨機率': 'ProbabilityOfPrecipitation'
        }

        for loc in locations_list:
            district = loc['LocationName']
            location_name = f"{county} {district}"
            
            # Map keyed by forecast_time
            time_series = {}

            for elem in loc.get('WeatherElement', []):
                elem_name = elem.get('ElementName')
                if elem_name not in element_mappings:
                    continue
                
                col_name = element_mappings[elem_name]
                val_key = element_keys[elem_name]
                
                for time_entry in elem.get('Time', []):
                    time_raw = time_entry.get('DataTime') or time_entry.get('StartTime')
                    if not time_raw:
                        continue
                        
                    # Standardize format to YYYY-MM-DD HH:MM:SS
                    try:
                        dt = datetime.strptime(time_raw[:19], "%Y-%m-%dT%H:%M:%S")
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        formatted_time = time_raw
                        
                    if formatted_time not in time_series:
                        time_series[formatted_time] = {
                            'location': location_name,
                            'forecast_time': formatted_time,
                            'temperature': None,
                            'humidity': None,
                            'rain_probability': None
                        }
                    
                    # Convert to numeric float or int
                    raw_val = time_entry.get('ElementValue', {}).get(val_key)
                    if raw_val is not None:
                        try:
                            time_series[formatted_time][col_name] = float(raw_val)
                        except ValueError:
                            time_series[formatted_time][col_name] = None
            
            # Append values to result list
            for time_key in time_series:
                parsed_rows.append(time_series[time_key])
                
        return parsed_rows
