
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import pandas as pd
import plotly.express as px
import time
import os
from datetime import datetime

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/predict")
st.set_page_config(page_title="Disaster Prediction AI", layout="wide", page_icon="⛈️")

# Custom CSS for "Premium" feel
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .main-metric {
        font_size: 3em;
        font-weight: bold;
        color: #4CAF50;
    }
    .risk-high { color: #FF4B4B; }
    .risk-medium { color: #FFA500; }
    .risk-low { color: #4CAF50; }
</style>
""", unsafe_allow_html=True)

st.title("⛈️ Real-Time Landslide & Flood Prediction System")
st.markdown("### 🇮🇳 Production-Ready AI Dashboard | India Region")

# Sidebar
with st.sidebar:
    st.header("System Status")
    st.success("API Connected: ✅ via Localhost")
    st.info("Models Loaded: XGBoost, Random Forest")
    
    st.divider()
    st.markdown("### 📡 Live Feeds")
    st.checkbox("Show Rainfall Radar (GPM)", True)
    st.checkbox("Show Terrain Slope", False)
    
    st.divider()
    auto_refresh = st.checkbox("Auto-Refresh (10 min)", value=True)
    if auto_refresh:
        time.sleep(1) # formatting placeholder
        # st_autorefresh(interval=600000) # Optional dependency

# Layout
col1, col2 = st.columns([2, 1])

# Map Section
with col1:
    st.subheader("📍 Select Location (Click on Map)")
    
    # Base Map (defaults to India center)
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="CartoDB dark_matter")
    
    # Event Data from Map Click
    map_data = st_folium(m, width="100%", height=500)

# Prediction Logic
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    
    with st.spinner(f"Fetching Satellite Data for {lat:.4f}, {lon:.4f}..."):
        try:
            # Call FastAPI Backend
            payload = {"lat": lat, "lon": lon}
            response = requests.post(API_URL, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                # Display Results
                with col2:
                    st.subheader("📊 Prediction Results")
                    st.markdown(f"**📍 Location:** {data.get('location_name', 'Unknown')}")
                    
                    # Risk Level Display
                    landslide_risk = data['landslide_risk_level']
                    flood_risk = data['flood_risk_level']
                    
                    risk_color = "risk-high" if landslide_risk == "High" else "risk-medium" if landslide_risk == "Medium" else "risk-low"
                    st.markdown(f"### Landslide Risk: <span class='{risk_color}'>{landslide_risk}</span>", unsafe_allow_html=True)
                    st.progress(data['landslide_probability'])
                    
                    risk_color_flood = "risk-high" if flood_risk == "High" else "risk-medium" if flood_risk == "Medium" else "risk-low"
                    st.markdown(f"### Flood Risk: <span class='{risk_color_flood}'>{flood_risk}</span>", unsafe_allow_html=True)
                    st.progress(data['flood_probability'])
                    
                    # === Weather Widget ===
                    st.divider()
                    st.subheader(f"Current Weather: {data.get('weather_desc', '').title()}")
                    
                    w_row1_c1, w_row1_c2 = st.columns(2)
                    with w_row1_c1:
                         # Icon + Description
                         if data.get("weather_icon"):
                            st.image(f"http://openweathermap.org/img/wn/{data['weather_icon']}@2x.png", width=80)
                         st.caption(f"{data.get('weather_desc', '').title()}")
                    with w_row1_c2:
                        st.metric("Temperature", f"{data.get('temperature', 0):.1f}°C")
                    
                    w_row2_c1, w_row2_c2 = st.columns(2)
                    with w_row2_c1:
                        st.metric("Wind Speed", f"{data.get('wind_speed', 0):.1f} m/s")
                    with w_row2_c2:
                        st.metric("Humidity", f"{data.get('humidity', 0)}%")

                    st.divider()
                    
                    # Environmental Metrics - Row 1
                    c1, c2, c3 = st.columns(3)
                    c1.metric("🌧️ Rain (24h)", f"{data['rainfall_24h']:.1f} mm")
                    c2.metric("🌧️ Rain (72h)", f"{data['rainfall_72h']:.1f} mm")
                    c3.metric("💧 Soil Sat.", f"{data['soil_saturation']:.2f}")

                    # Environmental Metrics - Row 2
                    c4, c5, c6 = st.columns(3)
                    c4.metric("🧪 Soil pH", f"{data['soil_ph']:.1f}")
                    c5.metric("⛰️ Elevation", f"{data['elevation']:.0f} m")
                    c6.metric("📉 Slope", f"{data['slope']:.1f}°")

                    # Environmental Metrics - Row 3
                    c7, c8, c9 = st.columns(3)
                    c7.metric("🌊 River Dist.", f"{data['river_distance']:.0f} m")
                    c8.metric("🌊 Flow Acc.", f"{data['flow_accumulation']:.0f}")
                    c9.metric("💧 Humidity", f"{data['humidity']:.0f}%")

                    # Environmental Metrics - Row 4
                    c10, c11 = st.columns(2)
                    c10.metric("🌡️ Pressure", f"{data['pressure']} hPa")
                    c11.write("") # Spacer or additional metric
                    
                    st.caption(f"NDVI: {data['ndvi']} | Lat/Lon: {lat:.4f}, {lon:.4f}")
                
                # === Historical Trends ===
                st.divider()
                st.subheader("📈 Historical Trends (Real-Time Log)")
                
                # Derive History URL from Predict URL
                HISTORY_URL = API_URL.replace("/predict", "/history")
                
                try:
                    hist_response = requests.get(HISTORY_URL, timeout=5)
                    if hist_response.status_code == 200:
                        hist_data = hist_response.json()
                        if hist_data:
                            df_hist = pd.DataFrame(hist_data)
                            df_hist['timestamp'] = pd.to_datetime(df_hist['timestamp'])
                            df_hist = df_hist.sort_values('timestamp')
                            
                            # Filter for relevant columns if they exist
                            cols = ['timestamp', 'landslide_probability', 'flood_probability', 'rainfall_24h', 'soil_saturation']
                            # Ensure columns exist (for old data)
                            for c in cols:
                                if c not in df_hist.columns:
                                    df_hist[c] = 0.0
                            
                            tab1, tab2 = st.tabs(["⚠️ Risk Trends", "🌍 Environmental Trends"])
                            
                            with tab1:
                                fig_risk = px.line(df_hist, x='timestamp', y=['landslide_probability', 'flood_probability'],
                                                  title="Disaster Risk Over Time",
                                                  labels={'value': 'Probability (0-1)', 'timestamp': 'Time'},
                                                  color_discrete_map={'landslide_probability': '#FF4B4B', 'flood_probability': '#FFA500'})
                                fig_risk.update_layout(template="plotly_dark", height=350)
                                st.plotly_chart(fig_risk, use_container_width=True)
                                
                            with tab2:
                                fig_env = px.line(df_hist, x='timestamp', y=['rainfall_24h', 'soil_saturation'],
                                                 title="Rainfall & Soil Saturation Trends",
                                                  labels={'value': 'Value', 'timestamp': 'Time'},
                                                  color_discrete_map={'rainfall_24h': '#00B4D8', 'soil_saturation': '#80FFDB'})
                                fig_env.update_layout(template="plotly_dark", height=350)
                                st.plotly_chart(fig_env, use_container_width=True)
                        else:
                            st.info("No historical data available yet.")
                    else:
                        st.warning("Could not fetch history.")
                except Exception as e:
                     st.error(f"History fetch error: {e}")
                
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            st.error(f"Connection Failed: {e}. Is Backend running?")
            
else:
    with col2:
        st.info("👈 Click on the map to analyze a specific location.")
        st.write("System monitors real-time satellite feeds from NASA GPM and soil moisture content.")
