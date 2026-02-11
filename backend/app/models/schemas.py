
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PredictionRequest(BaseModel):
    lat: float
    lon: float

class PredictionResponse(BaseModel):
    lat: float
    lon: float
    timestamp: datetime
    location_name: Optional[str] = "Unknown Location"
    
    # Environmental Data
    rainfall_1h: float
    rainfall_24h: float
    rainfall_72h: float = 0.0
    soil_saturation: float = 0.0
    flow_accumulation: float = 0.0
    river_distance: float = 0.0
    soil_ph: float = 0.0
    temperature: float = 0.0
    weather_desc: str = ""
    weather_icon: str = ""
    wind_speed: float = 0.0
    humidity: float
    pressure: float
    elevation: float
    slope: float
    ndvi: float
    
    # Predictions
    landslide_probability: float
    landslide_risk_level: str  # Low, Medium, High
    flood_probability: float
    flood_risk_level: str
    
    warnings: List[str] = []

class HealthCheck(BaseModel):
    status: str
    models_loaded: bool
