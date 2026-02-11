
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

def get_ee_river_distance(lat: float, lon: float):
    """
    Get distance to nearest river using Earth Engine HydroSHEDS.
    This is faster and more reliable than querying OSM API.
    """
    try:
        point = ee.Geometry.Point(lon, lat)
        
        # 1. Load HydroSHEDS Flow Accumulation
        # Rivers are defined where flow accumulation is high
        # We can also use 'WWF/HydroSHEDS/03VFD' for flow direction or 15ACC for accumulation
        hydrosheds = ee.Image("WWF/HydroSHEDS/15ACC")
        flow_acc = hydrosheds.select("b1")
        
        # 2. Define "River" mask (Threshold > 500 represents streams/rivers)
        # 1 where it IS a river, 0 elsewhere
        river_mask = flow_acc.gt(500)
        
        # 3. Compute Distance
        # fastDistanceTransform calculates distance to nearest non-zero pixel (the river)
        # Result is in pixels. multiply by scale to get meters.
        # fastDistanceTransform propagates distance.
        # Max distance 1024 pixels. At 450m (15 arc sec), that is ~450km. Plenty.
        
        dist_pixels = river_mask.fastDistanceTransform(1024).reproject(crs="EPSG:4326", scale=450)
        
        # Convert pixels to meters (approximate at the point location)
        # 15 arc-seconds is approx 450 meters at equator
        
        # Reduce at the point of interest
        # We use a larger scale to match the 15 arc-sec native resolution
        distance_val = dist_pixels.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=450
        ).getInfo().get("distance") 
        
        # Note: fastDistanceTransform output band is called "distance" by default?
        # No, it preserves bands?
        # Actually fastDistanceTransform returns an image where the value is distance in pixels.
        # The band name is likely 'distance' or same as input 'b1'.
        # Let's check documentation or assume it keeps name or uses 'distance'.
        # Safest way is to select the first band.
        
        # Wait, fastDistanceTransform returns units in PIXELS.
        # We need to multiply by pixel size in meters.
        # Pixel area sqrt is approx size.
        
        if distance_val is None:
             # Try getting raw value without explicit band name if reduceRegion returns dict
             val_dict = dist_pixels.reduceRegion(reducer=ee.Reducer.first(), geometry=point, scale=450).getInfo()
             if val_dict:
                 distance_val = list(val_dict.values())[0]
        
        if distance_val is not None:
            # Approximation: 1 pixel ~ 460m
            return float(distance_val) * 460.0
            
        return 5000.0 # Fallback if too far
        
    except Exception as e:
        logger.error(f"EE River Distance failed: {e}")
        print(f"DEBUG: EE River Distance Exception: {e}") # Print to console for visibility
        return 5000.0 # Safe fallback

def get_hydrological_features(lat: float, lon: float):
    """
    Fetch REAL hydrological features using Earth Engine and Open-Meteo.
    """
    # 1. Soil Saturation (Open-Meteo)
    om_data = get_open_meteo_flood_data(lat, lon)
    final_soil = om_data["soil_moisture"] 
    
    # 2. Flow Accumulation (Earth Engine)
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
        logger.error(f"EE Flow Acc failed: {e}")
        if om_data["river_discharge"] > 0:
             final_flow = om_data["river_discharge"] * 100 

    # 3. River Distance (Earth Engine)
    # Replaces the unstable OSM Overpass API call
    final_distance = get_ee_river_distance(lat, lon)
    
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
