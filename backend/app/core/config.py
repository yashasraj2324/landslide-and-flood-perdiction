
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Landslide & Flood Prediction API"
    VERSION: str = "1.0.0"

    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    EARTH_ENGINE_SERVICE_ACCOUNT: str = os.getenv("EARTH_ENGINE_SERVICE_ACCOUNT", "")
    EARTH_ENGINE_KEY_FILE: str = os.getenv("EARTH_ENGINE_KEY_FILE", r"")

    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "disaster_db")
    
    MODEL_PATH_LANDSLIDE: str = os.getenv("MODEL_PATH_LANDSLIDE", "../models/landslide_xgb.pkl")
    MODEL_PATH_FLOOD: str = os.getenv("MODEL_PATH_FLOOD", "../models/flood_model_v2_final.pkl")
    MODEL_PATH_THRESHOLD: str = os.getenv("MODEL_PATH_THRESHOLD", "../models/threshold.pkl")

settings = Settings()
