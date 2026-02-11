
import joblib
import pandas as pd
import numpy as np
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class ModelLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
            cls._instance.landslide_model = None
            cls._instance.flood_model = None
            cls._instance.threshold = None
            cls._instance._loaded = False
        return cls._instance

    def load_models(self):
        if self._loaded:
            return

        try:
            logger.info(f"Loading Landslide model from {settings.MODEL_PATH_LANDSLIDE}")
            self.landslide_model = joblib.load(settings.MODEL_PATH_LANDSLIDE)
            
            logger.info(f"Loading Flood model from {settings.MODEL_PATH_FLOOD}")
            self.flood_model = joblib.load(settings.MODEL_PATH_FLOOD)
            
            logger.info(f"Loading Thresholds from {settings.MODEL_PATH_THRESHOLD}")
            self.threshold = joblib.load(settings.MODEL_PATH_THRESHOLD)
            
            self._loaded = True
            logger.info("All models loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            # For development, we might not want to crash if models are missing, 
            # but for production this is critical.
            # raise e 

    def predict_landslide(self, features: dict):
        if not self.landslide_model:
            return 0.0, "Model not loaded"
            
        try:
            # Expected: ['elevation', 'rainfall', 'soil_ph', 'slope']
            feature_order = ['elevation', 'rainfall', 'soil_ph', 'slope']
            df = pd.DataFrame([features])
            
            # Reorder
            df = df[feature_order]
            
            prob = self.landslide_model.predict_proba(df)[:, 1][0]
            pred = self.landslide_model.predict(df)[0]
            return float(prob), int(pred)
        except Exception as e:
            logger.error(f"Landslide Prediction error: {e}")
            return 0.0, 0

    def predict_flood(self, features: dict):
        if not self.flood_model:
            return 0.0, "Model not loaded"
            
        try:
            # Expected: ['lat', 'lon', 'rain_24h', 'rain_72h', 'soil_saturation', 'elevation', 'slope', 'flow_accumulation', 'river_distance']
            feature_order = ['lat', 'lon', 'rain_24h', 'rain_72h', 'soil_saturation', 'elevation', 'slope', 'flow_accumulation', 'river_distance']
            
            df = pd.DataFrame([features])
            df = df[feature_order]
            
            prob = self.flood_model.predict_proba(df)[:, 1][0]
            return float(prob)
        except Exception as e:
            logger.error(f"Flood Prediction error: {e}")
            return 0.0

model_loader = ModelLoader()
