
import requests
import datetime
from ..core.config import settings
import ee
import logging
import os

logger = logging.getLogger(__name__)

def init_earth_engine():
    """Explicitly initialize Earth Engine with credentials."""
    # Try to initialize Earth Engine
    try:
        logger.info(f"Checking EE credentials: SA={settings.EARTH_ENGINE_SERVICE_ACCOUNT}, KeyFile={settings.EARTH_ENGINE_KEY_FILE}")
        if settings.EARTH_ENGINE_KEY_FILE:
            exists = os.path.exists(settings.EARTH_ENGINE_KEY_FILE)
            logger.info(f"Key file exists: {exists}")
        
        if settings.EARTH_ENGINE_SERVICE_ACCOUNT and settings.EARTH_ENGINE_KEY_FILE and os.path.exists(settings.EARTH_ENGINE_KEY_FILE):
            credentials = ee.ServiceAccountCredentials(settings.EARTH_ENGINE_SERVICE_ACCOUNT, settings.EARTH_ENGINE_KEY_FILE)
            ee.Initialize(credentials=credentials)
            logger.info("Earth Engine initialized with Service Account.")
        else:
            ee.Initialize()
            logger.info("Earth Engine initialized with default credentials.")
    except Exception as e:
        logger.warning(f"Earth Engine initialization failed: {e}. Ensure credentials are set.")

def get_elevation_slope(lat: float, lon: float):
    """
    Get elevation and slope from Earth Engine using SRTM or similar DEM.
    """
    try:
        point = ee.Geometry.Point(lon, lat)
        srtm = ee.Image("USGS/SRTMGL1_003")
        elevation = srtm.select("elevation").reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=30
        ).getInfo().get("elevation")
        
        slope_img = ee.Terrain.slope(srtm)
        slope = slope_img.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=30
        ).getInfo().get("slope")
        
        return elevation, slope
    except Exception as e:
        logger.error(f"Error fetching DEM data: {e}")
        return 0.0, 0.0  # Fallback

def get_rainfall_gpm(lat: float, lon: float, hours: int = 24):
    """
    Get accumulated rainfall from GPM (Global Precipitation Measurement) via Earth Engine.
    """
    try:
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(hours=hours)
        
        dataset = ee.ImageCollection("NASA/GPM_L3/IMERG_V06") \
            .filterDate(start_date, end_date) \
            .select("precipitationCal")
        
        # Sum over the period
        total_precip = dataset.sum()
        
        point = ee.Geometry.Point(lon, lat)
        precip_value = total_precip.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=10000
        ).getInfo().get("precipitationCal")
        
        return precip_value if precip_value else 0.0
    except Exception as e:
        logger.error(f"Error fetching GPM rainfall: {e}")
        return 0.0


def get_open_meteo_flood_data(lat: float, lon: float):
    """
    Fetch river discharge and soil moisture from Open-Meteo.
    """
    try:
        # 1. Flood API for Discharge
        flood_url = f"https://flood-api.open-meteo.com/v1/flood?latitude={lat}&longitude={lon}&daily=river_discharge_mean&forecast_days=1"
        flood_res = requests.get(flood_url).json()
        discharge = flood_res.get("daily", {}).get("river_discharge_mean", [0.0])[0]
        
        # Handle None values from API
        if discharge is None:
            discharge = 0.0
            
        logger.info(f"Open-Meteo Discharge for {lat},{lon}: {discharge} m3/s")
        
        # 2. Forecast API for Soil Moisture
        # soil_moisture_0_to_1cm is volumetric (m³/m³) usually 0.0-0.5
        meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=soil_moisture_0_to_1cm&forecast_days=1"
        meteo_res = requests.get(meteo_url).json()
        soil_moisture = meteo_res.get("hourly", {}).get("soil_moisture_0_to_1cm", [0.0])[0]
        
        return {
            "river_discharge": discharge, # Proxy for flow_accumulation
            "soil_moisture": soil_moisture # Proxy for soil_saturation
        }
    except Exception as e:
        logger.error(f"Open-Meteo fetch failed: {e}")
        return {"river_discharge": 0.0, "soil_moisture": 0.0}



from geopy.distance import geodesic

def get_osm_river_distance(lat: float, lon: float):
    """
    Calculate the GEOMETRIC distance to the nearest river using OpenStreetMap (Overpass API).
    This provides the real physical distance, not a proxy.
    """
    try:
        # Search for waterways within ~5km radius (approx 0.05 degrees)
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        (
          way["waterway"="river"](around:5000, {lat}, {lon});
          way["waterway"="stream"](around:2000, {lat}, {lon});
          relation["waterway"="river"](around:5000, {lat}, {lon});
        );
        out geom;
        """
        response = requests.get(overpass_url, params={'data': query}, timeout=10)
        data = response.json()
        
        min_distance = 5000.0 # Default max search radius
        
        elements = data.get("elements", [])
        if not elements:
            return 5000.0
            
        user_loc = (lat, lon)
        
        for element in elements:
            # Check geometry points
            if "geometry" in element:
                for pt in element["geometry"]:
                    river_pt = (pt["lat"], pt["lon"])
                    dist = geodesic(user_loc, river_pt).meters
                    if dist < min_distance:
                        min_distance = dist
            elif "lat" in element and "lon" in element:
                 # Nodes
                 river_pt = (element["lat"], element["lon"])
                 dist = geodesic(user_loc, river_pt).meters
                 if dist < min_distance:
                        min_distance = dist

        return min_distance

    except Exception as e:
        logger.error(f"OSM River fetch failed: {e}")
        return 5000.0 # Fail safe

def get_hydrological_features(lat: float, lon: float):
    """
    Fetch REAL hydrological features:
    - Flow Accumulation: Earth Engine HydroSHEDS (Real catchment data)
    - River Distance: OpenStreetMap (Real geometric distance)
    - Soil Saturation: Open-Meteo (Real soil moisture forecast)
    """
    # 1. Soil Saturation from Open-Meteo (Best live source)
    om_data = get_open_meteo_flood_data(lat, lon)
    final_soil = om_data["soil_moisture"] 

    # 2. Real River Distance from OSM
    final_distance = get_osm_river_distance(lat, lon)
    
    # 3. Real Flow Accumulation from Earth Engine
    final_flow = 0.0
    try:
        point = ee.Geometry.Point(lon, lat)
        hydrosheds = ee.Image("WWF/HydroSHEDS/15ACC")
        flow_acc = hydrosheds.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point, scale=500
        ).getInfo().get("b1", 0.0)
        
        if flow_acc is not None:
             final_flow = flow_acc
    except Exception as e:
        logger.error(f"EE Hydro fetch failed: {e}")
        # Only fallback if EE fails
        if om_data["river_discharge"] > 0:
             final_flow = om_data["river_discharge"] * 100 

    return {
        "flow_accumulation": final_flow,
        "river_distance": final_distance,
        "soil_saturation": final_soil
    }
def get_weather_data(lat: float, lon: float):
    """
    Fetch current weather data from OpenWeatherMap.
    """
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={settings.OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            weather_main = data.get("weather", [{}])[0]
            main_data = data.get("main", {})
            wind_data = data.get("wind", {})
            
            return {
                "humidity": main_data.get("humidity", 0),
                "pressure": main_data.get("pressure", 0),
                "temperature": main_data.get("temp", 0.0),
                "weather_desc": weather_main.get("description", "Unknown"),
                "weather_icon": weather_main.get("icon", ""),
                "wind_speed": wind_data.get("speed", 0.0),
                "rainfall_1h": data.get("rain", {}).get("1h", 0.0)
            }
        else:
            logger.error(f"OpenWeatherMap error: {data}")
            return {
                "humidity": 0, "pressure": 0, "temperature": 0.0, 
                "weather_desc": "N/A", "weather_icon": "", "wind_speed": 0.0, 
                "rainfall_1h": 0.0
            }
    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        return {
            "humidity": 0, "pressure": 0, "temperature": 0.0, 
            "weather_desc": "Error", "weather_icon": "", "wind_speed": 0.0, 
            "rainfall_1h": 0.0
        }
