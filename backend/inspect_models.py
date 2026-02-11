
import joblib
import pandas as pd
import xgboost
import sys

def inspect(path):
    print(f"--- Inspecting {path} ---")
    try:
        model = joblib.load(path)
        print(f"Type: {type(model)}")
        
        if hasattr(model, "feature_names_in_"):
            print(f"Feature Names (sklearn/standard): {model.feature_names_in_}")
        elif hasattr(model, "get_booster"):
            print(f"Feature Names (xgboost booster): {model.get_booster().feature_names}")
        elif hasattr(model, "booster_"):
             print(f"Feature Names (lgbm booster): {model.booster_.feature_name()}")
        else:
            print("Could not find feature names directly.")
            try:
                # Try accessing internal xgboost booster attributes 
                print(f"XGBoost features: {model.get_booster().feature_names}")
            except:
                pass
    except Exception as e:
        print(f"Error loading: {e}")

if __name__ == "__main__":
    inspect("../models/landslide_xgb.pkl")
    inspect("../models/flood_model_v2_final.pkl")
