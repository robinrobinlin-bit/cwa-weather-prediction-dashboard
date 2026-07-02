import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add parent directory to path so src can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.database import get_locations, get_forecasts

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
            pass

# Load Windy API Key from .env
load_dotenv()
WINDY_API_KEY = os.environ.get("WINDY_API_KEY")

# Latitude and Longitude mapping for Yilan County districts
LOCATION_COORDS = {
    "宜蘭縣 宜蘭市": (24.753707, 121.745083),
    "宜蘭縣 羅東鎮": (24.678673, 121.758763),
    "宜蘭縣 蘇澳鎮": (24.595673, 121.844374),
    "宜蘭縣 頭城鎮": (24.856984, 121.821915),
    "宜蘭縣 礁溪鄉": (24.819794, 121.766324),
    "宜蘭縣 壯圍鄉": (24.743132, 121.810574),
    "宜蘭縣 員山鄉": (24.741005, 121.688177),
    "宜蘭縣 冬山鄉": (24.634125, 121.792474),
    "宜蘭縣 五結鄉": (24.684126, 121.802474),
    "宜蘭縣 三星鄉": (24.667086, 121.650893),
    "宜蘭縣 大同鄉": (24.676646, 121.606713),
    "宜蘭縣 南澳鄉": (24.460834, 121.800043)
}

# Page Configuration
st.set_page_config(
    page_title="CWA Weather Forecast Dashboard",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling (Dark Theme & Glassmorphism Cards)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 50% 50%, rgba(26, 32, 53, 1) 0%, rgba(11, 15, 30, 1) 100%);
        color: #F8FAFC;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 5px 0 25px rgba(0, 0, 0, 0.4);
    }
    
    /* Title text styling */
    .dashboard-title {
        background: linear-gradient(135deg, #38BDF8 0%, #3B82F6 60%, #8B5CF6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.6rem;
        margin-bottom: 0.5rem;
    }
    
    /* Card Container Styles */
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(56, 189, 248, 0.35);
        box-shadow: 0 15px 35px rgba(56, 189, 248, 0.12);
    }
    
    .kpi-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        color: #94A3B8;
        font-weight: 600;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    
    .kpi-value {
        font-size: 2.4rem;
        font-weight: 800;
        color: #FFFFFF;
    }
    
    .kpi-unit {
        font-size: 1.1rem;
        color: #38BDF8;
        font-weight: 500;
        margin-left: 3px;
    }
    
    .kpi-desc {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to render a premium KPI Card
def render_kpi(col, title, value, unit, desc):
    col.markdown(f"""
    <div class="glass-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
        <div class="kpi-desc">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

# Fetch location choices from database
db_locations = get_locations()

# Check if data exists
if not db_locations:
    st.error("No weather data found in the database. Please run the data collector or POST /api/weather/update first.")
    st.stop()

# Sidebar Setup
st.sidebar.markdown("<h2 style='color:#38BDF8; font-weight:800; text-align:center;'>⛅ Forecast Hub</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='color:#64748B; font-size:0.85rem; text-align:center; margin-bottom:2rem;'>Taiwan CWA Weather Predictor</p>", unsafe_allow_html=True)

# Page Navigation selector
pages = ["🏠 Home Overview", "📋 Detailed Forecasts", "📈 Plotly Charts", "🗺️ Weather Map"]
selected_page = st.sidebar.radio("Navigation Page", pages)

st.sidebar.markdown("---")

# Location selector in the sidebar
selected_loc = st.sidebar.selectbox("Select Location", db_locations)

st.sidebar.markdown("<p style='text-align: center; color: #475569; font-size: 0.75rem; margin-top: 5rem;'>© 2026 CWA Forecast Project</p>", unsafe_allow_html=True)

# Fetch forecasts for selected location
forecasts = get_forecasts(location=selected_loc)
df = pd.DataFrame(forecasts)
if not df.empty:
    df['forecast_time'] = pd.to_datetime(df['forecast_time'])
    df = df.sort_values(by='forecast_time')

# ----------------- PAGE 1: HOME OVERVIEW -----------------
if selected_page == "🏠 Home Overview":
    st.markdown(f"<h1 class='dashboard-title'>Weather Overview: {selected_loc}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8; margin-bottom:2rem;'>Quick overview of current conditions and 7-day trends.</p>", unsafe_allow_html=True)
    
    if df.empty:
        st.warning("No data found for this location.")
    else:
        # Determine current temperature as the first forecast entry
        current_temp = df.iloc[0]['temperature']
        current_humidity = df.iloc[0]['humidity']
        current_time = df.iloc[0]['forecast_time'].strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate stats for the rest of the 7-day period
        avg_temp = df['temperature'].mean()
        max_temp = df['temperature'].max()
        min_temp = df['temperature'].min()
        
        # Render top metric cards
        k1, k2, k3, k4 = st.columns(4)
        render_kpi(k1, "Current Temperature", f"{current_temp:.1f}", "°C", f"Forecasted at {current_time}")
        render_kpi(k2, "Current Humidity", f"{current_humidity:.0f}", "%", "Relative air humidity level")
        render_kpi(k3, "Avg Temp (7-Day)", f"{avg_temp:.1f}", "°C", "Expected weekly average")
        render_kpi(k4, "Max Temp (7-Day)", f"{max_temp:.1f}", "°C", f"Expected weekly peak (Min: {min_temp:.1f}°C)")
        
        st.write("")
        st.write("")
        
        col_desc, col_quick = st.columns([5, 3])
        with col_desc:
            st.subheader("Welcome to the Weather Dashboard")
            st.write(
                "This dashboard displays live forecast data retrieved from the Central Weather Administration (CWA) "
                "OpenData API. You can choose different districts from the sidebar to inspect regional temperatures, "
                "relative humidity variations, and precipitation profiles."
            )
            st.info("💡 **Navigation Hint**: Head to the **Detailed Forecasts** tab to search data tables, or open **Plotly Charts** to visualize 7-day temperature trends and rainfall chances!")
            
        with col_quick:
            st.subheader("Data Info")
            latest_time = df['created_at'].max() if 'created_at' in df.columns else "Unknown"
            st.write(f"**Location Selected**: `{selected_loc}`")
            st.write(f"**Sync Date**: `{latest_time}`")
            st.write(f"**Total Records**: `{len(df)}` intervals")

# ----------------- PAGE 2: DETAILED FORECASTS -----------------
elif selected_page == "📋 Detailed Forecasts":
    st.markdown(f"<h1 class='dashboard-title'>Forecast Data: {selected_loc}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8; margin-bottom:2rem;'>Sortable and filterable dataset of CWA forecasts.</p>", unsafe_allow_html=True)
    
    if df.empty:
        st.warning("No data found for this location.")
    else:
        # Display data explorer table
        display_cols = ['forecast_time', 'temperature', 'humidity', 'rain_probability']
        df_display = df[display_cols].copy()
        df_display.columns = ['Forecast Time', 'Temperature (°C)', 'Humidity (%)', 'Rain Probability (%)']
        
        st.dataframe(
            df_display.style.format({
                'Temperature (°C)': '{:.1f}',
                'Humidity (%)': '{:.0f}',
                'Rain Probability (%)': lambda x: f'{x:.0f}' if pd.notnull(x) else '-'
            }),
            use_container_width=True
        )
        
        # Download utilities
        csv_data = df_display.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Download Forecast Table as CSV",
            data=csv_data,
            file_name=f"forecast_{selected_loc.replace(' ', '_')}.csv",
            mime='text/csv'
        )

# ----------------- PAGE 3: PLOTLY CHARTS -----------------
elif selected_page == "📈 Plotly Charts":
    st.markdown(f"<h1 class='dashboard-title'>Forecast Visualizations: {selected_loc}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8; margin-bottom:2rem;'>Interactive visualization of temperature and precipitation probabilities.</p>", unsafe_allow_html=True)
    
    if df.empty:
        st.warning("No data found for this location.")
    else:
        # 1. 7-Day Line Chart
        fig_line = px.line(
            df, x='forecast_time', y='temperature',
            title='7-Day Temperature Forecast Trend',
            labels={'temperature': 'Temperature (°C)', 'forecast_time': 'Time'},
            template='plotly_dark'
        )
        fig_line.update_traces(line_color='#38BDF8', line_width=3, mode='lines+markers')
        fig_line.update_layout(
            hovermode='x unified',
            plot_bgcolor='rgba(30, 41, 59, 0.25)',
            paper_bgcolor='rgba(0, 0, 0, 0)'
        )
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.write("")
        st.write("")
        
        # 2. Rain Probability Bar Chart
        df_rain = df.dropna(subset=['rain_probability'])
        if not df_rain.empty:
            fig_bar = px.bar(
                df_rain, x='forecast_time', y='rain_probability',
                title='3-Hour Interval Rain Probability Profile',
                labels={'rain_probability': 'Probability of Rain (%)', 'forecast_time': 'Time'},
                template='plotly_dark'
            )
            fig_bar.update_traces(marker_color='#3B82F6', opacity=0.85)
            fig_bar.update_layout(
                plot_bgcolor='rgba(30, 41, 59, 0.25)',
                paper_bgcolor='rgba(0, 0, 0, 0)'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No rain probability data available for this location to render the chart.")

# ----------------- PAGE 4: WEATHER MAP -----------------
elif selected_page == "🗺️ Weather Map":
    st.markdown(f"<h1 class='dashboard-title'>Windy Weather Map: {selected_loc}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8; margin-bottom:2rem;'>Interactive Windy Map synchronized with the selected CWA station location.</p>", unsafe_allow_html=True)
    
    # Check if WINDY_API_KEY is found (logged as per requirements)
    if WINDY_API_KEY:
        st.sidebar.success("Windy API Key loaded from .env")
    else:
        st.sidebar.warning("Windy API Key not set in .env. Using free visualization layer.")

    # Layer selector
    map_layer = st.selectbox("Select Map Overlay Layer", ["Temperature", "Wind", "Rain", "Cloud"])
    
    layer_mapping = {
        "Temperature": "temp",
        "Wind": "wind",
        "Rain": "rain",
        "Cloud": "clouds"
    }
    
    windy_layer = layer_mapping[map_layer]
    
    # Get coordinates of selected location, fallback to Yilan County center
    coords = LOCATION_COORDS.get(selected_loc, (24.6766, 121.7588))
    lat, lon = coords
    
    # Windy iframe embed URL centered on selection
    windy_url = f"https://embed.windy.com/embed2.html?lat={lat}&lon={lon}&zoom=9&level=surface&overlay={windy_layer}&menu=&message=true&marker=true&calendar=now&pressure=true&type=map&location=coordinates&detail=true&metricWind=default&metricTemp=default"
    
    # Create side by side columns: map and CWA current stats
    col_map, col_details = st.columns([5, 2])
    
    with col_map:
        st.markdown(f"""
        <div style="border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
            <iframe src="{windy_url}" width="100%" height="580" frameborder="0"></iframe>
        </div>
        """, unsafe_allow_html=True)
        
    with col_details:
        st.markdown("<h4 style='color:#38BDF8;'>Synchronized CWA Data</h4>", unsafe_allow_html=True)
        if not df.empty:
            current_rec = df.iloc[0]
            curr_temp = current_rec['temperature']
            curr_hum = current_rec['humidity']
            curr_rain = current_rec['rain_probability']
            curr_time = current_rec['forecast_time'].strftime("%Y-%m-%d %H:%M:%S")
            
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.3); padding: 16px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 12px;">
                <p style='color:#94A3B8; font-size:0.8rem; margin:0;'>Forecast Time</p>
                <p style='font-size:1.1rem; font-weight:700; margin:0; color:#FFFFFF;'>{curr_time}</p>
            </div>
            <div style="background: rgba(30, 41, 59, 0.3); padding: 16px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 12px;">
                <p style='color:#94A3B8; font-size:0.8rem; margin:0;'>CWA Temperature</p>
                <p style='font-size:1.5rem; font-weight:800; margin:0; color:#F43F5E;'>{curr_temp:.1f}°C</p>
            </div>
            <div style="background: rgba(30, 41, 59, 0.3); padding: 16px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 12px;">
                <p style='color:#94A3B8; font-size:0.8rem; margin:0;'>CWA Relative Humidity</p>
                <p style='font-size:1.5rem; font-weight:800; margin:0; color:#38BDF8;'>{curr_hum:.0f}%</p>
            </div>
            <div style="background: rgba(30, 41, 59, 0.3); padding: 16px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05);">
                <p style='color:#94A3B8; font-size:0.8rem; margin:0;'>CWA Rain Probability</p>
                <p style='font-size:1.5rem; font-weight:800; margin:0; color:#3B82F6;'>{f"{curr_rain:.0f}%" if pd.notnull(curr_rain) else "-"}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No aligned CWA data found.")
