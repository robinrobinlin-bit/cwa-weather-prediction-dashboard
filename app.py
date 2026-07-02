import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Taiwan AI Weather Forecast Dashboard",
    page_icon="🇹🇼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS styling (Dark glassmorphism theme)
st.markdown("""
<style>
    /* Custom main font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Premium background & layout */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(20, 25, 45, 1) 0%, rgba(10, 12, 22, 1) 100%);
        color: #E2E8F0;
    }
    
    /* Sidebar customization */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.9);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
    }
    
    /* Header gradient text */
    .header-title {
        background: linear-gradient(135deg, #38BDF8 0%, #3B82F6 50%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
    }
    
    /* Glassmorphism KPI Cards */
    .kpi-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease-in-out;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 12px 40px 0 rgba(56, 189, 248, 0.15);
    }
    
    .kpi-title {
        font-size: 0.9rem;
        text-transform: uppercase;
        color: #94A3B8;
        font-weight: 600;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    
    .kpi-unit {
        font-size: 1rem;
        font-weight: 400;
        color: #38BDF8;
        margin-left: 4px;
    }
    
    .kpi-footer {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# API Endpoint base URL
API_URL = "http://127.0.0.1:8000"

def get_api_data(endpoint, params=None):
    try:
        response = requests.get(f"{API_URL}{endpoint}", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception:
        return None

def trigger_post_api(endpoint):
    try:
        response = requests.post(f"{API_URL}{endpoint}", timeout=30)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Load sidebar controls
st.sidebar.markdown("<h2 style='text-align: center; color: #38BDF8; font-weight: 800;'>🇹🇼 AI Weather</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #64748B; font-size: 0.85rem; margin-bottom: 2rem;'>Taiwan Forecast & Prediction System</p>", unsafe_allow_html=True)

# Sidebar Navigation Selector
pages = [
    "🏠 Home Overview",
    "📊 CWA Forecasts",
    "🤖 AI Predictions",
    "🎯 Actual vs Predicted",
    "🗺️ Windy Weather Map",
    "📐 Model Evaluation",
    "📁 Data Explorer"
]
selected_page = st.sidebar.radio("Navigation Menu", pages)

# Location list loading helper
locations_res = get_api_data("/api/weather/locations")
locations = locations_res.get("locations", []) if locations_res else []

# Fallback in case API fails
if not locations:
    locations = ["宜蘭縣 宜蘭市"]

# Main Sidebar selection for location if applicable
selected_loc = None
if selected_page in ["📊 CWA Forecasts", "🤖 AI Predictions", "🎯 Actual vs Predicted", "📁 Data Explorer"]:
    selected_loc = st.sidebar.selectbox("Select Township / District", locations)

st.sidebar.markdown("---")
# Action Section in Sidebar
st.sidebar.markdown("<p style='color:#94A3B8; font-weight: 600; font-size: 0.85rem;'>System Actions</p>", unsafe_allow_html=True)
if st.sidebar.button("🔄 Sync CWA Live Data"):
    with st.spinner("Connecting to CWA Open Data API..."):
        res = get_api_data("/api/cwa/fetch")
        if res and res.get("status") == "success":
            st.sidebar.success("CWA Data Synced!")
            st.rerun()
        else:
            st.sidebar.error("Sync failed. Check CWA API keys.")

if st.sidebar.button("🧠 Retrain Prediction Model"):
    with st.spinner("Engineering features & training model..."):
        res = trigger_post_api("/api/model/train")
        if res and res.get("status") == "success":
            st.sidebar.success("Model trained successfully!")
            st.rerun()
        else:
            st.sidebar.error(f"Training failed: {res.get('message') if res else 'API error'}")

st.sidebar.markdown(f"<p style='text-align: center; color: #475569; font-size: 0.75rem; margin-top: 3rem;'>Server Status: Online<br>© 2026 AI Weather Project</p>", unsafe_allow_html=True)

# Helper function to render a KPI card
def render_kpi(col, title, value, unit, footer):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
        <div class="kpi-footer">{footer}</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- PAGE 1: HOME OVERVIEW -----------------
if selected_page == "🏠 Home Overview":
    st.markdown("<h1 class='header-title'>CWA OpenData + Windy API + AI Forecast Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 1.1rem; margin-bottom: 2rem;'>Taiwan Temperature Prediction & Interactive Weather Visualization Platform</p>", unsafe_allow_html=True)
    
    # Load all forecasts to compute KPIs
    all_data_res = get_api_data("/api/weather/forecast")
    if all_data_res and all_data_res.get("data"):
        df_all = pd.DataFrame(all_data_res["data"])
        total_locs = df_all['location_name'].nunique()
        avg_temp = df_all['temperature'].mean()
        max_temp = df_all['temperature'].max()
        avg_humidity = df_all['humidity'].mean()
    else:
        df_all = None
        total_locs = 0
        avg_temp = 0.0
        max_temp = 0.0
        avg_humidity = 0.0
        
    metrics_res = get_api_data("/api/model/metrics")
    model_name = metrics_res.get("model_name", "RandomForestRegressor") if metrics_res else "RandomForestRegressor"
    r2_score = metrics_res.get("r2_score", 0.0) if metrics_res else 0.0
    mae = metrics_res.get("mae", 0.0) if metrics_res else 0.0
    
    # Top KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    render_kpi(col1, "Locations Monitored", f"{total_locs}", "districts", f"CWA F-D0047-001 datasets")
    render_kpi(col2, "Avg Temp (Forecast)", f"{avg_temp:.1f}", "°C", "7-day average prediction")
    render_kpi(col3, "Max Temperature", f"{max_temp:.1f}", "°C", "Highest forecasted peak")
    render_kpi(col4, "AI Model Accuracy", f"{r2_score*100:.1f}", "%", f"{model_name} R² Score (MAE: {mae:.2f}°C)")
    
    st.write("")
    st.write("")
    
    # Overview Description Columns
    l_col, r_col = st.columns([3, 2])
    with l_col:
        st.subheader("Project Highlights")
        st.markdown("""
        - **Official Forecast Data Source**: Real-time retrieval of local township forecast datasets (`F-D0047-00Series`) directly from the **Central Weather Administration (CWA)**.
        - **Machine Learning Integration**: Built-in feature engineering extracting temporal variables, lag values, and rolling window trends to run **RandomForestRegressor** predictions.
        - **Premium Visualizations**: Fully responsive charts evaluating predictions, residual spreads, and parameter correlations using Plotly.
        - **Windy Map Overlay**: Interactive Leaflet maps embedded directly to explore spatial forecasts.
        """)
        
        st.info("💡 **Getting Started**: Use the sidebar menu to navigate through detailed forecast pages or trigger dynamic synchronizations and model retrains!")
        
    with r_col:
        st.subheader("Data Synced Info")
        if df_all is not None and len(df_all) > 0:
            latest_rec = df_all['created_at'].max()
            first_time = df_all['forecast_time'].min()
            last_time = df_all['forecast_time'].max()
            
            st.write(f"**CWA OpenData Sync Time**: `{latest_rec}`")
            st.write(f"**Forecast Window Start**: `{first_time}`")
            st.write(f"**Forecast Window End**: `{last_time}`")
            st.write(f"**Total Records Loaded**: `{len(df_all)}` rows")
        else:
            st.warning("No data found. Click 'Sync CWA Live Data' in the sidebar to load the initial dataset.")

# ----------------- PAGE 2: CWA FORECASTS -----------------
elif selected_page == "📊 CWA Forecasts":
    st.markdown(f"<h1 class='header-title'>CWA Official Forecast: {selected_loc}</h1>", unsafe_allow_html=True)
    
    # Load forecast data for selected location
    forecast_res = get_api_data("/api/weather/forecast", {"location": selected_loc})
    if forecast_res and forecast_res.get("data"):
        df = pd.DataFrame(forecast_res["data"])
        df['forecast_time'] = pd.to_datetime(df['forecast_time'])
        
        # Display KPI highlights for the location
        k1, k2, k3 = st.columns(3)
        current_temp = df.iloc[0]['temperature']
        current_desc = df.iloc[0]['weather_description'] or "No details"
        current_wind = df.iloc[0]['wind_speed'] or 0.0
        current_wind_dir = df.iloc[0]['wind_direction'] or "Unknown"
        
        render_kpi(k1, "Initial Temp", f"{current_temp:.1f}", "°C", "Starting forecast point")
        render_kpi(k2, "Initial Wind", f"{current_wind:.1f}", "m/s", f"Heading: {current_wind_dir}")
        render_kpi(k3, "Current Condition", f"{current_desc[:12]}...", "", f"{current_desc[:40]}")
        
        st.write("")
        
        # Line chart for Temperature
        fig_temp = px.line(
            df, x='forecast_time', y='temperature',
            title='7-Day Hourly Temperature Trend',
            labels={'temperature': 'Temperature (°C)', 'forecast_time': 'Time'},
            template='plotly_dark'
        )
        fig_temp.update_traces(line_color='#38BDF8', line_width=3)
        fig_temp.update_layout(
            hovermode='x unified',
            plot_bgcolor='rgba(30, 41, 59, 0.2)',
            paper_bgcolor='rgba(0, 0, 0, 0)'
        )
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Rain probability and humidity charts
        col_rain, col_hum = st.columns(2)
        with col_rain:
            # Filters rows having rain probability data
            df_rain = df.dropna(subset=['rain_probability'])
            if len(df_rain) > 0:
                fig_rain = px.bar(
                    df_rain, x='forecast_time', y='rain_probability',
                    title='3-Hour Probability of Precipitation',
                    labels={'rain_probability': 'Probability (%)', 'forecast_time': 'Time'},
                    template='plotly_dark'
                )
                fig_rain.update_traces(marker_color='#3B82F6')
                fig_rain.update_layout(
                    plot_bgcolor='rgba(30, 41, 59, 0.2)',
                    paper_bgcolor='rgba(0, 0, 0, 0)'
                )
                st.plotly_chart(fig_rain, use_container_width=True)
            else:
                st.info("Rain probability data not available for this location.")
                
        with col_hum:
            df_hum = df.dropna(subset=['humidity'])
            if len(df_hum) > 0:
                fig_hum = px.line(
                    df_hum, x='forecast_time', y='humidity',
                    title='Relative Humidity Profile',
                    labels={'humidity': 'Humidity (%)', 'forecast_time': 'Time'},
                    template='plotly_dark'
                )
                fig_hum.update_traces(line_color='#8B5CF6', line_width=2)
                fig_hum.update_layout(
                    plot_bgcolor='rgba(30, 41, 59, 0.2)',
                    paper_bgcolor='rgba(0, 0, 0, 0)'
                )
                st.plotly_chart(fig_hum, use_container_width=True)
            else:
                st.info("Humidity profile data not available.")
    else:
        st.warning("No forecast data available. Make sure to sync CWA data.")

# ----------------- PAGE 3: AI TEMPERATURE PREDICTION -----------------
elif selected_page == "🤖 AI Predictions":
    st.markdown(f"<h1 class='header-title'>AI Temperature Prediction: {selected_loc}</h1>", unsafe_allow_html=True)
    
    # Fetch forecasts and predictions
    forecast_res = get_api_data("/api/weather/forecast", {"location": selected_loc})
    pred_res = get_api_data("/api/weather/predict", {"location": selected_loc})
    
    if forecast_res and pred_res and forecast_res.get("data") and pred_res.get("predictions"):
        df_forecast = pd.DataFrame(forecast_res["data"])
        df_pred = pd.DataFrame(pred_res["predictions"])
        
        # Merge datasets on time to align them
        df_forecast['forecast_time'] = pd.to_datetime(df_forecast['forecast_time'])
        df_pred['prediction_time'] = pd.to_datetime(df_pred['prediction_time'])
        
        df_merged = pd.merge(
            df_forecast, df_pred, 
            left_on='forecast_time', right_on='prediction_time',
            suffixes=('_cwa', '_ai')
        )
        
        # Stats metrics
        mae_val = df_merged['mae'].iloc[0]
        rmse_val = df_merged['rmse'].iloc[0]
        
        k1, k2, k3 = st.columns(3)
        render_kpi(k1, "Prediction MAE", f"{mae_val:.2f}", "°C", "Mean Absolute Error")
        render_kpi(k2, "Prediction RMSE", f"{rmse_val:.2f}", "°C", "Root Mean Square Error")
        render_kpi(k3, "Inference Model", "RF Regressor", "", "Scikit-Learn RandomForest")
        
        st.write("")
        
        # Combined line chart
        fig_predict = go.Figure()
        fig_predict.add_trace(go.Scatter(
            x=df_merged['forecast_time'], y=df_merged['temperature'],
            name='CWA Forecast (Baseline Target)',
            line=dict(color='#38BDF8', width=3),
            mode='lines+markers'
        ))
        fig_predict.add_trace(go.Scatter(
            x=df_merged['forecast_time'], y=df_merged['predicted_temperature'],
            name='AI Prediction (Random Forest)',
            line=dict(color='#F43F5E', width=3, dash='dash'),
            mode='lines+markers'
        ))
        
        fig_predict.update_layout(
            title='AI Predicted Temperature vs Official CWA Values',
            xaxis_title='Time',
            yaxis_title='Temperature (°C)',
            template='plotly_dark',
            hovermode='x unified',
            plot_bgcolor='rgba(30, 41, 59, 0.2)',
            paper_bgcolor='rgba(0, 0, 0, 0)'
        )
        st.plotly_chart(fig_predict, use_container_width=True)
        
        # Predictive Model Explanation Box
        st.subheader("How does the prediction model work?")
        st.markdown("""
        The system trains a **Random Forest Regressor** using lag features.
        The key inputs used to predict the temperature at a specific hour $t$ include:
        1. **Temperature Lag $t-1$**: The temperature recorded at the previous forecast interval.
        2. **Rolling Mean Temperature**: The average temperature over the preceding 3 intervals.
        3. **Historical Climate Features**: Hour of the day, day of the week, and month.
        4. **Atmospheric Covariates**: Forecasted relative humidity, rain probability, and wind speed.
        
        This translates weather trends into interactive ML features, correcting sudden variations and validating CWA patterns.
        """)
    else:
        st.warning("Model predictions not found. Make sure to train the model in the sidebar.")

# ----------------- PAGE 4: ACTUAL VS PREDICTED -----------------
elif selected_page == "🎯 Actual vs Predicted":
    st.markdown(f"<h1 class='header-title'>Model Error Analysis: {selected_loc}</h1>", unsafe_allow_html=True)
    
    forecast_res = get_api_data("/api/weather/forecast", {"location": selected_loc})
    pred_res = get_api_data("/api/weather/predict", {"location": selected_loc})
    
    if forecast_res and pred_res and forecast_res.get("data") and pred_res.get("predictions"):
        df_forecast = pd.DataFrame(forecast_res["data"])
        df_pred = pd.DataFrame(pred_res["predictions"])
        
        df_forecast['forecast_time'] = pd.to_datetime(df_forecast['forecast_time'])
        df_pred['prediction_time'] = pd.to_datetime(df_pred['prediction_time'])
        
        df_merged = pd.merge(
            df_forecast, df_pred, 
            left_on='forecast_time', right_on='prediction_time'
        )
        
        df_merged['residual'] = df_merged['temperature'] - df_merged['predicted_temperature']
        
        col_scatter, col_residual = st.columns(2)
        
        with col_scatter:
            # Scatter plot Actual vs Predicted
            fig_scatter = px.scatter(
                df_merged, x='temperature', y='predicted_temperature',
                trendline="ols",
                title='Scatter Plot: Actual (CWA) vs AI Predicted Temperature',
                labels={'temperature': 'Actual CWA Temperature (°C)', 'predicted_temperature': 'AI Predicted Temperature (°C)'},
                template='plotly_dark'
            )
            fig_scatter.update_traces(marker=dict(color='#8B5CF6', size=8, opacity=0.8))
            fig_scatter.update_layout(
                plot_bgcolor='rgba(30, 41, 59, 0.2)',
                paper_bgcolor='rgba(0, 0, 0, 0)'
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with col_residual:
            # Residual plot
            fig_res = px.bar(
                df_merged, x='forecast_time', y='residual',
                title='Residual Plot (Actual - Predicted Error)',
                labels={'residual': 'Error (°C)', 'forecast_time': 'Time'},
                template='plotly_dark'
            )
            fig_res.update_traces(marker_color='#F43F5E')
            fig_res.update_layout(
                plot_bgcolor='rgba(30, 41, 59, 0.2)',
                paper_bgcolor='rgba(0, 0, 0, 0)'
            )
            st.plotly_chart(fig_res, use_container_width=True)
            
        st.write("")
        st.subheader("Residual Statistics Summary")
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        res_mean = df_merged['residual'].mean()
        res_std = df_merged['residual'].std()
        res_max = df_merged['residual'].abs().max()
        
        render_kpi(stats_col1, "Mean Error Bias", f"{res_mean:.4f}", "°C", "Close to 0 indicates unbiased prediction")
        render_kpi(stats_col2, "Error Standard Dev", f"{res_std:.4f}", "°C", "Distribution spread of residuals")
        render_kpi(stats_col3, "Max Absolute Error", f"{res_max:.2f}", "°C", "Maximum deviation recorded")
    else:
        st.warning("No prediction datasets available for analysis.")

# ----------------- PAGE 5: WINDY MAP -----------------
elif selected_page == "🗺️ Windy Weather Map":
    st.markdown("<h1 class='header-title'>Windy Interactive Weather Map</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; font-size: 1.1rem; margin-bottom: 2rem;'>Taiwan Live Weather Model Maps & Flow Visualizations</p>", unsafe_allow_html=True)
    
    # Layer selector
    overlay_layer = st.selectbox("Select Weather Layer Map", ["temperature", "wind", "rain", "clouds", "radar"])
    
    # Map layers maps to Windy query values
    layer_map = {
        "temperature": "temp",
        "wind": "wind",
        "rain": "rain",
        "clouds": "clouds",
        "radar": "radar"
    }
    
    windy_layer = layer_map[overlay_layer]
    
    # Embed Windy map Centered on Taiwan
    windy_iframe_url = f"https://embed.windy.com/embed2.html?lat=23.9738&lon=120.9820&zoom=7&level=surface&overlay={windy_layer}&menu=&message=true&marker=true&calendar=now&pressure=true&type=map&location=coordinates&detail=true&metricWind=default&metricTemp=default"
    
    st.markdown(f"""
    <div style="border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
        <iframe src="{windy_iframe_url}" width="100%" height="650" frameborder="0"></iframe>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.info("💡 **Windy API Info**: Use the bottom timeline inside the Windy frame to control forecast animations, play winds, or zoom in on specific regions in Taiwan.")

# ----------------- PAGE 6: MODEL EVALUATION -----------------
elif selected_page == "📐 Model Evaluation":
    st.markdown("<h1 class='header-title'>AI Model Performance Evaluation</h1>", unsafe_allow_html=True)
    
    metrics_res = get_api_data("/api/model/metrics")
    if metrics_res and metrics_res.get("mae") is not None:
        mae_v = metrics_res.get("mae")
        rmse_v = metrics_res.get("rmse")
        r2_v = metrics_res.get("r2_score")
        mape_v = metrics_res.get("mape", 0.0)
        trained_t = metrics_res.get("trained_at", "Unknown")
        
        st.write(f"**Latest training run date**: `{trained_t}`")
        
        k1, k2, k3, k4 = st.columns(4)
        render_kpi(k1, "Mean Absolute Error (MAE)", f"{mae_v:.4f}", "°C", "Average prediction error offset")
        render_kpi(k2, "Root Mean Square Error (RMSE)", f"{rmse_v:.4f}", "°C", "Penalizes larger outliers")
        render_kpi(k3, "R² Determination Coeff", f"{r2_v*100:.1f}", "%", "Variance explained by the model")
        render_kpi(k4, "Mean Abs Percent Error (MAPE)", f"{mape_v:.2f}", "%", "Error relative to true values")
        
        # Load feature importance from saved pickle
        import os
        import pickle
        from src.train_model import MODEL_PATH
        
        st.write("")
        st.subheader("Feature Importance Analysis")
        
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, 'rb') as f:
                model_data = pickle.load(f)
            
            model = model_data['model']
            features = model_data['features']
            importances = model.feature_importances_
            
            # Create feature importance dataframe
            df_imp = pd.DataFrame({
                'Feature': features,
                'Importance': importances
            }).sort_values(by='Importance', ascending=True)
            
            # Map features to reader friendly labels
            feature_labels = {
                'hour': 'Hour of day',
                'day_of_week': 'Day of week',
                'month': 'Month',
                'previous_temperature': 'Lag Temperature (t-1)',
                'humidity': 'Relative Humidity',
                'rain_probability': 'Precipitation Probability',
                'wind_speed': 'Wind Speed',
                'location_encoded': 'Location code (encoded)',
                'rolling_mean_temperature': 'Rolling Mean Temp (3 intervals)'
            }
            df_imp['Feature Label'] = df_imp['Feature'].map(feature_labels)
            
            fig_imp = px.bar(
                df_imp, x='Importance', y='Feature Label',
                orientation='h',
                title='Feature Importances (Random Forest Regressor)',
                labels={'Importance': 'Relative Importance', 'Feature Label': 'Predictive Feature'},
                template='plotly_dark'
            )
            fig_imp.update_traces(marker_color='#8B5CF6')
            fig_imp.update_layout(
                plot_bgcolor='rgba(30, 41, 59, 0.2)',
                paper_bgcolor='rgba(0, 0, 0, 0)'
            )
            st.plotly_chart(fig_imp, use_container_width=True)
        else:
            st.info("Train the model in the sidebar to visualize feature importances.")
    else:
        st.warning("No model training metrics found in the database. Please trigger retraining in the sidebar first.")

# ----------------- PAGE 7: DATA EXPLORER -----------------
elif selected_page == "📁 Data Explorer":
    st.markdown(f"<h1 class='header-title'>Weather Data Explorer: {selected_loc}</h1>", unsafe_allow_html=True)
    
    forecast_res = get_api_data("/api/weather/forecast", {"location": selected_loc})
    if forecast_res and forecast_res.get("data"):
        df = pd.DataFrame(forecast_res["data"])
        
        # Select columns to display
        display_cols = [
            'forecast_time', 'temperature', 'humidity', 'rain_probability',
            'wind_speed', 'wind_direction', 'weather_description', 'created_at'
        ]
        
        # Display data table
        st.dataframe(
            df[display_cols].style.format({
                'temperature': '{:.1f}',
                'humidity': '{:.1f}',
                'rain_probability': '{:.1f}',
                'wind_speed': '{:.1f}'
            }),
            use_container_width=True
        )
        
        # Download utilities
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv_data,
                file_name=f"weather_{selected_loc.replace(' ', '_')}.csv",
                mime='text/csv'
            )
    else:
        st.warning("No data found for this location.")
