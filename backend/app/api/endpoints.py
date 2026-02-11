
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from ..services.weather_service import get_weather_data, get_elevation_slope, get_rainfall_gpm, get_hydrological_features
from ..services.model_loader import model_loader
from ..models.schemas import PredictionRequest, PredictionResponse, HealthCheck
from ..db.database import get_database
from ..db.models import PredictionDocument
from datetime import datetime
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

router = APIRouter()
logger = logging.getLogger(__name__)

def get_location_name(lat, lon):
    try:
        geolocator = Nominatim(user_agent="deriveit_landslide_app")
        location = geolocator.reverse((lat, lon), exactly_one=True, language='en')
        return location.address if location else "Unknown Location"
    except Exception as e:
        logger.warning(f"Geocoding failed: {e}")
        return "Unknown Location"

async def save_prediction_mongo(data: dict):
    try:
        db = get_database()
        # Convert Pydantic model to dict, or construct manually if stricter control needed
        doc = PredictionDocument(
            lat=data['lat'],
            lon=data['lon'],
            location_name=data.get('location_name', "Unknown Location"),
            rainfall_24h=data['rainfall_24h'],
            slope=data['slope'],
            landslide_prob=data['landslide_probability'],
            flood_prob=data['flood_probability'],
            risk_level=data['landslide_risk_level'],
            timestamp=datetime.utcnow()
        )
        await db.predictions.insert_one(doc.dict())
    except Exception as e:
        logger.error(f"Failed to save to MongoDB: {e}")

@router.get("/health", response_model=HealthCheck)
def health_check():
    return {
        "status": "ok", 
        "models_loaded": model_loader._loaded
    }

def determine_risk_level(prob: float) -> str:
    if prob < 0.3: return "Low"
    elif prob < 0.7: return "Medium"
    else: return "High"

@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest, background_tasks: BackgroundTasks):
    lat, lon = request.lat, request.lon
    
    # 1. Fetch Data
    weather = get_weather_data(lat, lon)
    elevation, slope = get_elevation_slope(lat, lon)
    rainfall_gpm_24h = get_rainfall_gpm(lat, lon, hours=24)
    # rainfall_gpm_72h = get_rainfall_gpm(lat, lon, hours=72) # Optional, strictly needed for flood model
    
    # New Hydrological Features
    hydro = get_hydrological_features(lat, lon)
    
    # Get Location Name
    location_name = get_location_name(lat, lon)
    
    # 2. Feature Engineering
    total_rainfall_24h = max(rainfall_gpm_24h, weather.get("rainfall_1h", 0) * 24)
    # Estimate 72h based on 24h if API is slow, or fetch real data. For speed, we estimate.
    total_rainfall_72h = total_rainfall_24h * 1.5 # Placeholder logic
    
    # --- LANDSLIDE MODEL PREPARATION ---
    # Expected: ['elevation', 'rainfall', 'soil_ph', 'slope']
    # Note: 'rainfall' usually implies intensity or recent accumulation. Using 24h.
    # 'soil_ph': Not available via standard live satellite APIs easily. Using neutral 7.0 or regional avg.
    landslide_features = {
        "elevation": elevation,
        "rainfall": total_rainfall_24h,
        "soil_ph": 6.5, # Default slightly acidic/neutral
        "slope": slope
    }
    
    # --- FLOOD MODEL PREPARATION ---
    # Expected: ['lat', 'lon', 'rain_24h', 'rain_72h', 'soil_saturation', 'elevation', 'slope', 'flow_accumulation', 'river_distance']
    flood_features = {
        "lat": lat,
        "lon": lon,
        "rain_24h": total_rainfall_24h,
        "rain_72h": total_rainfall_72h,
        "soil_saturation": hydro.get("soil_saturation", 0.5),
        "elevation": elevation,
        "slope": slope,
        "flow_accumulation": hydro.get("flow_accumulation", 0.0),
        "river_distance": hydro.get("river_distance", 1000.0)
    }
    
    # 3. Predict
    # We need to update model_loader to accept specific feature dicts or just pass the dicts directly 
    # if we update the signatures. Let's assume we pass these dicts.
    
    landslide_prob, _ = model_loader.predict_landslide(landslide_features)
    flood_prob = model_loader.predict_flood(flood_features)
    
    risk_level_landslide = determine_risk_level(landslide_prob)
    risk_level_flood = determine_risk_level(flood_prob)

    response_data = {
        "lat": lat,
        "lon": lon,
        "location_name": location_name,
        "timestamp": datetime.utcnow(),
        "rainfall_1h": weather.get("rainfall_1h", 0),
        "rainfall_24h": total_rainfall_24h,
        "rainfall_72h": total_rainfall_72h,
        "soil_saturation": hydro.get("soil_saturation", 0.0),
        "flow_accumulation": hydro.get("flow_accumulation", 0.0),
        "river_distance": hydro.get("river_distance", 1000.0),
        "soil_ph": 6.5,
        "temperature": weather.get("temperature", 0.0),
        "weather_desc": weather.get("weather_desc", ""),
        "weather_icon": weather.get("weather_icon", ""),
        "wind_speed": weather.get("wind_speed", 0.0),
        "humidity": weather.get("humidity", 0),
        "pressure": weather.get("pressure", 0),
        "elevation": elevation,
        "slope": slope,
        "ndvi": 0.5, # Placeholder
        "landslide_probability": landslide_prob,
        "landslide_risk_level": risk_level_landslide,
        "flood_probability": flood_prob,
        "flood_risk_level": risk_level_flood,
        "warnings": []
    }

    # 4. Save to DB in background
    background_tasks.add_task(save_prediction_mongo, response_data)

    return response_data
    
@router.get("/history")
async def get_history():
    db = get_database()
    cursor = db.predictions.find().sort("timestamp", -1).limit(50)
    history = await cursor.to_list(length=50)
    # Convert _id to string for JSON serialization
    for doc in history:
        doc["_id"] = str(doc["_id"])
    return history
