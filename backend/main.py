
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.services.model_loader import model_loader
from app.services.weather_service import init_earth_engine
from app.db.database import connect_to_mongo, close_mongo_connection
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Landslide & Flood Prediction API",
    description="Real-time disaster prediction using Satellite Data and ML",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(endpoints.router, prefix="/api/v1")

# Background Scheduler
scheduler = AsyncIOScheduler()

async def periodic_data_refresh():
    logger.info("Executing periodic background data refresh...")
    pass

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    await connect_to_mongo()
    model_loader.load_models()
    init_earth_engine()
    scheduler.add_job(periodic_data_refresh, "interval", minutes=15)
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()
    scheduler.shutdown()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Disaster Prediction API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
