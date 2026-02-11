
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime

# === CONFIGURATION ===
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/predict")
HISTORY_URL = API_URL.replace("/predict", "/history")

st.set_page_config(
    page_title="Disaster Prediction AI", 
    layout="wide", 
    page_icon="⛈️",
    initial_sidebar_state="expanded"
)

# === CUSTOM CSS FOR PROFESSIONAL DASHBOARD ===
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Card Container Styling */
    div[data-testid="stContainer"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }

    /* Metric Values */
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        color: #e6edf3;
    }
    
    /* Metric Labels */
    [data-testid="stMetricLabel"] {
        color: #8b949e;
        font-size: 0.85rem !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        border-radius: 4px 4px 0px 0px;
        color: #8b949e;
    }
    .stTabs [aria-selected="true"] {
        background-color: #161b22;
        color: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)

# === HELPER FUNCTIONS ===
def create_gauge(value, title, color_stops):
    """Creates a gauge chart for risk visualization"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,  # Convert 0-1 to Percentage
        title={'text': title, 'font': {'size': 18, 'color': "#e6edf3"}},
        number={'suffix': "%", 'font': {'color': "#e6edf3"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#30363d"},
            'bar': {'color': "#1f6feb"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#30363d",
            'steps': color_stops,
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': value * 100
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#e6edf3"},
        margin=dict(l=20, r=20, t=30, b=20),
        height=180
    )
    return fig

# === HEADER ===
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("⛈️ Sentinel AI: Disaster Prediction")
    st.caption("Real-Time Landslide & Flood Monitoring System | Live Production Environment")
with col_h2:
    st.write("") 
    st.markdown(f"**System Status:** 🟢 Online")
    st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S UTC')}")

# === SIDEBAR ===
with st.sidebar:
    st.header("⚙️ Controls")
    
    with st.container():
        st.subheader("Data Layers")
        show_radar = st.toggle("Rainfall Radar (GPM)", True)
        show_slope = st.toggle("Terrain Slope Map", False)
    
    with st.container():
        st.subheader("API Status")
        if st.button("Ping Backend"):
            try:
                requests.get(API_URL.replace("/predict", "/health"), timeout=2)
                st.success("Backend Connected")
            except:
                st.error("Backend Unreachable")

# === MAIN LAYOUT ===
col_map, col_dash = st.columns([1.5, 1.2])

# --- LEFT: MAP SECTION ---
with col_map:
    with st.container():
        st.subheader("📍 Select Location")
        
        # Base Map
        m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="CartoDB dark_matter")
        
        if show_slope:
            folium.TileLayer(
                tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                attr='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
                name='Terrain'
            ).add_to(m)
            
        # Capture Click
        map_data = st_folium(m, width="100%", height=650)

# --- RIGHT: DASHBOARD SECTION ---
with col_dash:
    # Check if user clicked the map
    if map_data and map_data.get("last_clicked"):
        lat = map_data["last_clicked"]["lat"]
        lon = map_data["last_clicked"]["lng"]
        
        st.info(f"Analyzing Coordinates: **{lat:.4f}, {lon:.4f}**")
        
        with st.spinner("Fetching Satellite & Sensor Data..."):
            try:
                # 1. PREDICTION API CALL
                payload = {"lat": lat, "lon": lon}
                response = requests.post(API_URL, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # === ROW 1: RISK GAUGES ===
                    st.subheader("⚠️ Risk Assessment")
                    r1, r2 = st.columns(2)
                    
                    with r1:
                        # Landslide Gauge
                        fig_ls = create_gauge(
                            data.get('landslide_probability', 0), 
                            "Landslide Risk", 
                            [{'range': [0, 50], 'color': "#238636"}, 
                             {'range': [50, 80], 'color': "#d29922"}, 
                             {'range': [80, 100], 'color': "#da3633"}]
                        )
                        st.plotly_chart(fig_ls, use_container_width=True, config={'displayModeBar': False})
                        st.caption(f"Risk Level: **{data.get('landslide_risk_level', 'Unknown')}**")

                    with r2:
                        # Flood Gauge
                        fig_fl = create_gauge(
                            data.get('flood_probability', 0), 
                            "Flood Risk",
                            [{'range': [0, 50], 'color': "#238636"}, 
                             {'range': [50, 80], 'color': "#d29922"}, 
                             {'range': [80, 100], 'color': "#1f6feb"}]
                        )
                        st.plotly_chart(fig_fl, use_container_width=True, config={'displayModeBar': False})
                        st.caption(f"Risk Level: **{data.get('flood_risk_level', 'Unknown')}**")
                    
                    # === ROW 2: ENVIRONMENTAL METRICS ===
                    st.subheader("🌍 Environmental Telemetry")
                    
                    # Weather Card
                    with st.container():
                        c1, c2 = st.columns([1, 3])
                        with c1:
                             # Display icon if available from API, else generic
                             icon_code = data.get('weather_icon', '01d')
                             st.image(f"http://openweathermap.org/img/wn/{icon_code}@2x.png", width=80)
                        with c2:
                             st.markdown(f"#### {data.get('weather_desc', 'Clear').title()}")
                             st.caption(f"Temp: {data.get('temperature', 0)}°C | Wind: {data.get('wind_speed', 0)} m/s")

                    # Metrics Grid
                    with st.container():
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Rain (24h)", f"{data.get('rainfall_24h', 0):.1f} mm")
                        m2.metric("Soil Saturation", f"{data.get('soil_saturation', 0):.2f}")
                        m3.metric("Slope", f"{data.get('slope', 0):.1f}°")
                        
                        m4, m5, m6 = st.columns(3)
                        m4.metric("Elevation", f"{data.get('elevation', 0)} m")
                        m5.metric("River Dist.", f"{data.get('river_distance', 0):.0f} m")
                        m6.metric("Flow Acc.", f"{data.get('flow_accumulation', 0):.0f}")

                    # === ROW 3: HISTORICAL DATA ===
                    st.subheader("📈 Historical Trends")
                    
                    try:
                        # 2. HISTORY API CALL
                        # Pass lat/lon to filter history if supported by backend, otherwise it returns global history
                        hist_response = requests.get(HISTORY_URL, params={"lat": lat, "lon": lon}, timeout=10)
                        
                        if hist_response.status_code == 200:
                            hist_data = hist_response.json()
                            if hist_data:
                                df_hist = pd.DataFrame(hist_data)
                                
                                # Normalize column names (Backend uses 'landslide_prob', Frontend expects 'landslide_probability')
                                col_map = {
                                    'landslide_prob': 'landslide_probability',
                                    'flood_prob': 'flood_probability',
                                    'rain_24h': 'rainfall_24h'
                                }
                                df_hist.rename(columns=col_map, inplace=True)
                                
                                if 'timestamp' in df_hist.columns and 'landslide_probability' in df_hist.columns:
                                    df_hist['timestamp'] = pd.to_datetime(df_hist['timestamp'])
                                    
                                    # Plot Area Chart
                                    fig_hist = px.area(
                                        df_hist, 
                                        x='timestamp', 
                                        y=['landslide_probability', 'flood_probability'],
                                        labels={'value': 'Probability', 'timestamp': 'Time'},
                                        color_discrete_map={'landslide_probability': '#da3633', 'flood_probability': '#1f6feb'}
                                    )
                                    fig_hist.update_layout(
                                        template="plotly_dark", 
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        height=250,
                                        margin=dict(l=0, r=0, t=10, b=0),
                                        legend=dict(orientation="h", y=1.1)
                                    )
                                    st.plotly_chart(fig_hist, use_container_width=True)
                                else:
                                    st.warning("Historical data missing required columns for plotting.")
                            else:
                                st.info("No historical records found for this location.")
                        else:
                            st.warning("Could not fetch historical trends.")
                            
                    except Exception as e:
                        st.error(f"History API Error: {str(e)}")

                else:
                    st.error(f"Prediction API Error: {response.status_code}")
                    st.text(response.text)
            
            except requests.exceptions.ConnectionError:
                st.error("🚨 Connection Error: Is the Backend API running?")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

    else:
        # EMPTY STATE (Waiting for user click)
        with st.container():
            st.info("👈 **Waiting for Input**")
            st.markdown("""
            Please click on the map to select a location for analysis.
            
            **System Capabilities:**
            * Real-time Rainfall Analysis (GPM)
            * Soil Moisture & Saturation Levels
            * Topological Slope & Elevation Data
            """)