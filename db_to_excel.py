import sqlite3
import pandas as pd

def main():
    db_file = 'weatherdb'
    excel_file = 'weather_data.xlsx'
    
    print(f"Connecting to SQLite database: {db_file}...")
    try:
        conn = sqlite3.connect(db_file)
        
        # Read the table into a pandas DataFrame
        print("Reading data from 'weather_forecasts' table...")
        df = pd.read_sql_query("SELECT * FROM weather_forecasts", conn)
        
        # Close the connection
        conn.close()
        
        print(f"Exporting data to Excel: {excel_file}...")
        # Save to Excel
        df.to_excel(excel_file, index=False, sheet_name='Weather Forecasts')
        
        print(f"Successfully converted database to Excel! File saved as '{excel_file}'.")
        
    except Exception as e:
        print(f"Error during database to Excel conversion: {e}")

if __name__ == '__main__':
    main()
