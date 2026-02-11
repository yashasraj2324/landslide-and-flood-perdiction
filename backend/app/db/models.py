
# Validating for Mongo if needed, but schemas.py covers Pydantic models.
# This file is less critical now but we can keep a reference model for clarity if needed.
# For now, we will just use schemas.PredictionResponse + timestamp for storage.
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class PredictionDocument(BaseModel):
    lat: float
    lon: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location_name: Optional[str] = "Unknown Location"
    rainfall_24h: float
    slope: float
    landslide_prob: float
    flood_prob: float
    risk_level: str
    
    class Config:
        schema_extra = {
            "example": {
                "lat": 20.5,
                "lon": 78.9,
                "timestamp": "2023-10-27T10:00:00",
                "rainfall_24h": 12.5,
                "slope": 15.0,
                "landslide_prob": 0.1,
                "flood_prob": 0.05,
                "risk_level": "Low"
            }
        }
