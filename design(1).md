# design.md

# Taiwan Weather Prediction & Visualization System
## CWA OpenData + Windy API + AI Forecast Dashboard

---

## 1. Project Overview

This project builds a weather prediction and visualization platform using Taiwan CWA OpenData as the main data source and Windy API as the interactive weather map visualization layer.

The system collects temperature forecast data from CWA, stores it in a database, performs data preprocessing, trains prediction models, and displays results through an interactive dashboard.

---

## 2. Project Goal

Build an AI weather dashboard that can:

1. Fetch CWA temperature forecast data.
2. Store historical and forecast data.
3. Predict future temperature trends.
4. Compare actual CWA data vs AI-predicted values.
5. Visualize weather information using charts and Windy API maps.
6. Provide a clean web dashboard for portfolio or homework presentation.

---

## 3. Recommended Tech Stack

| Layer | Technology |
|---|---|
| Data Source | CWA OpenData |
| Map Visualization | Windy API |
| Backend API | FastAPI |
| Database | SQLite for beginner, PostgreSQL for production |
| Data Processing | Python, Pandas |
| Machine Learning | Scikit-learn, XGBoost, LightGBM |
| Dashboard | Streamlit or React |
| Charts | Plotly |
| Scheduler | APScheduler or Cron |
| Deployment | Render, Railway, Vercel, Streamlit Cloud |

---

## 4. System Architecture

```text
┌────────────────────────────┐
│        CWA OpenData         │
│ Temperature Forecast API    │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│     Data Collector          │
│ Python requests module      │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│     Data Preprocessing      │
│ clean / transform / feature │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│          Database           │
│ SQLite / PostgreSQL         │
└───────┬──────────────┬─────┘
        │              │
        ▼              ▼
┌───────────────┐   ┌────────────────┐
│ ML Prediction │   │ FastAPI Backend │
│ Model Service │   │ REST API        │
└───────┬───────┘   └────────┬───────┘
        │                    │
        └──────────┬─────────┘
                   ▼
┌────────────────────────────────────┐
│         Dashboard Frontend          │
│ Streamlit / React + Plotly          │
└─────────────────┬──────────────────┘
                  │
                  ▼
┌────────────────────────────────────┐
│             Windy API Map           │
│ Temperature / Wind / Rain Layers    │
└────────────────────────────────────┘
```

---

## 5. Main Data Source

### 5.1 CWA OpenData

Recommended datasets:

| Purpose | Dataset |
|---|---|
| 36-hour city forecast | F-C0032-001 |
| 7-day township forecast | F-D0047 series |
| Real-time weather station data | O-A0003-001 |
| Rainfall data | O-A0002-001 |
| Weather warning | W-C0033-001 |

For this project, the recommended starting dataset is:

```text
F-D0047 series
```

because it provides township-level forecast data and is more suitable for 7-day temperature visualization.

---

## 6. Windy API Role

Windy API should be used mainly as a visualization layer, not as the primary prediction data source.

### Windy API usage

1. Show Taiwan weather map.
2. Display temperature layer.
3. Display wind layer.
4. Display rain/cloud layer.
5. Provide interactive zoom and pan.
6. Compare map view with CWA forecast charts.

### Important

CWA should be the official data source.

Windy API should be used for map visualization and user experience enhancement.

---

## 7. Data Flow

```text
Step 1: Call CWA API
Step 2: Parse JSON response
Step 3: Extract location, time, temperature, humidity, rain probability
Step 4: Clean missing values
Step 5: Store data into database
Step 6: Generate ML features
Step 7: Train prediction model
Step 8: Predict next temperature values
Step 9: Send results to dashboard API
Step 10: Display charts and Windy map
```

---

## 8. Database Design

### 8.1 Table: weather_forecast

```sql
CREATE TABLE weather_forecast (
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 8.2 Table: weather_prediction

```sql
CREATE TABLE weather_prediction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_name TEXT NOT NULL,
    prediction_time DATETIME NOT NULL,
    predicted_temperature REAL,
    model_name TEXT,
    mae REAL,
    rmse REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 8.3 Table: model_metrics

```sql
CREATE TABLE model_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    target_variable TEXT,
    mae REAL,
    rmse REAL,
    r2_score REAL,
    mape REAL,
    trained_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 9. API Design

### 9.1 Fetch CWA Data

```http
GET /api/cwa/fetch
```

Purpose:

Fetch latest CWA weather forecast and save to database.

Response:

```json
{
  "status": "success",
  "message": "CWA data fetched successfully"
}
```

---

### 9.2 Get Weather Forecast

```http
GET /api/weather/forecast?location=Taichung
```

Response:

```json
{
  "location": "Taichung",
  "data": [
    {
      "forecast_time": "2026-07-02 12:00:00",
      "temperature": 32,
      "rain_probability": 30
    }
  ]
}
```

---

### 9.3 Get AI Prediction

```http
GET /api/weather/predict?location=Taichung
```

Response:

```json
{
  "location": "Taichung",
  "model": "XGBoost",
  "predictions": [
    {
      "prediction_time": "2026-07-03 12:00:00",
      "predicted_temperature": 33.2
    }
  ]
}
```

---

### 9.4 Get Model Metrics

```http
GET /api/model/metrics
```

Response:

```json
{
  "model_name": "RandomForestRegressor",
  "mae": 1.2,
  "rmse": 1.8,
  "r2_score": 0.86
}
```

---

## 10. Machine Learning Design

### 10.1 Prediction Target

Primary target:

```text
temperature
```

Optional targets:

```text
min_temperature
max_temperature
rain_probability
humidity
```

---

### 10.2 Feature Engineering

Recommended features:

| Feature | Description |
|---|---|
| hour | hour of forecast time |
| day_of_week | weekday |
| month | seasonal information |
| previous_temperature | lag feature |
| humidity | humidity |
| rain_probability | rainfall probability |
| wind_speed | wind speed |
| location_encoded | encoded location |
| rolling_mean_temperature | moving average temperature |

---

### 10.3 Recommended Models

Start simple:

1. Linear Regression
2. Random Forest Regressor
3. XGBoost Regressor
4. LightGBM Regressor
5. LSTM, optional advanced model

Recommended beginner model:

```text
RandomForestRegressor
```

Recommended stronger model:

```text
XGBoostRegressor
```

---

## 11. Visualization Design

### 11.1 Dashboard Pages

```text
Page 1: Home
Page 2: CWA Forecast
Page 3: AI Temperature Prediction
Page 4: Actual vs Predicted
Page 5: Windy Weather Map
Page 6: Model Evaluation
Page 7: Data Explorer
```

---

### 11.2 Dashboard Components

| Component | Visualization |
|---|---|
| Current temperature | KPI card |
| 7-day temperature forecast | Line chart |
| Rain probability | Bar chart |
| Actual vs predicted temperature | Multi-line chart |
| Prediction error | Residual chart |
| Model performance | MAE / RMSE / R2 cards |
| Taiwan map | Windy API |
| Feature importance | Horizontal bar chart |

---

## 12. Windy API Frontend Example

Use Windy API inside a dashboard page.

```html
<div id="windy" style="width: 100%; height: 600px;"></div>

<script src="https://api.windy.com/assets/map-forecast/libBoot.js"></script>

<script>
const options = {
    key: "YOUR_WINDY_API_KEY",
    lat: 24.1477,
    lon: 120.6736,
    zoom: 8,
    overlay: "temp"
};

windyInit(options, windyAPI => {
    const { map } = windyAPI;
});
</script>
```

---

## 13. Suggested Folder Structure

```text
weather_prediction_project/
│
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── design.md
├── .env
│
├── backend/
│   ├── api.py
│   ├── database.py
│   ├── models.py
│   └── schemas.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── weather.db
│
├── src/
│   ├── cwa_client.py
│   ├── data_cleaning.py
│   ├── feature_engineering.py
│   ├── train_model.py
│   ├── predict.py
│   └── visualization.py
│
├── dashboard/
│   ├── home.py
│   ├── forecast_page.py
│   ├── prediction_page.py
│   ├── windy_map_page.py
│   └── model_evaluation_page.py
│
├── models/
│   └── temperature_model.pkl
│
├── outputs/
│   ├── figures/
│   ├── reports/
│   └── predictions.csv
│
└── tests/
    ├── test_cwa_client.py
    ├── test_model.py
    └── test_api.py
```

---

## 14. Environment Variables

Create a `.env` file.

```env
CWA_API_KEY=your_cwa_api_key_here
WINDY_API_KEY=your_windy_api_key_here
DATABASE_URL=sqlite:///data/weather.db
```

Important:

Never upload `.env` to GitHub.

Add this to `.gitignore`:

```text
.env
data/weather.db
models/*.pkl
__pycache__/
```

---

## 15. Development Steps

### Phase 1: Data Collection

1. Create CWA API key.
2. Write `src/cwa_client.py`.
3. Fetch CWA forecast data.
4. Save raw JSON to `data/raw/`.
5. Parse useful fields.
6. Save clean data to SQLite.

---

### Phase 2: Dashboard Basic Version

1. Build Streamlit dashboard.
2. Show 7-day temperature line chart.
3. Show rain probability bar chart.
4. Show data table.
5. Add location selector.

---

### Phase 3: Machine Learning

1. Prepare training data.
2. Create lag features.
3. Train RandomForestRegressor.
4. Evaluate MAE, RMSE, R2.
5. Save model as `.pkl`.
6. Display actual vs predicted chart.

---

### Phase 4: Windy API Integration

1. Create Windy API key.
2. Add Windy map page.
3. Show temperature layer.
4. Center map on selected Taiwan city.
5. Combine CWA chart + Windy map view.

---

### Phase 5: Deployment

1. Push project to GitHub.
2. Deploy dashboard to Streamlit Cloud or Render.
3. Add environment variables.
4. Test API keys.
5. Add screenshots and demo video to README.

---

## 16. Recommended Minimum Viable Product

MVP should include:

1. CWA API data fetch.
2. SQLite storage.
3. 7-day temperature chart.
4. AI temperature prediction.
5. Actual vs predicted chart.
6. Windy temperature map.
7. Model metrics.

---

## 17. Suggested README Demo Section

```markdown
## Demo Features

- Taiwan CWA weather forecast data
- 7-day temperature visualization
- AI temperature prediction
- Actual vs predicted comparison
- Windy API interactive weather map
- Model performance dashboard
```

---

## 18. Success Criteria

The project is successful if:

1. CWA data can be fetched successfully.
2. Weather data is stored in database.
3. Dashboard shows temperature trends.
4. Prediction model runs without error.
5. Actual vs predicted chart is visible.
6. Windy API map loads correctly.
7. Project can be deployed online.

---

## 19. Future Improvements

1. Add ESP32 + DHT11 sensor data.
2. Compare CWA data with real sensor data.
3. Add LSTM or Transformer model.
4. Add LINE Bot weather alert.
5. Add rainfall prediction.
6. Add typhoon warning visualization.
7. Add county-level map comparison.
8. Add automatic daily report generation.

---

## 20. Notes for Antigravity / AI Coding Agent

Please implement this project step by step.

Priority order:

1. Build working CWA data fetcher.
2. Build database schema.
3. Build Streamlit dashboard.
4. Add Plotly charts.
5. Add simple ML prediction.
6. Add Windy API map.
7. Add README and screenshots.

Avoid overengineering in the first version.

Use simple, readable Python code.

Make sure all API keys are stored in `.env`.

Do not hardcode API keys in source code.
