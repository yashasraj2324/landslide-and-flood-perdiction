
# Backend Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
# Removed libgdal-dev as it's heavy and might not be strictly needed if pkl models are simple,
# but keeping build-essential. If geopandas needs it, we might need to add it back or use a geospatial base image.
# For now, minimal.
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
