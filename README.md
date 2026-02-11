# 🌍 Real-Time Landslide & Flood Prediction System  
**DeriveIT — AI-Powered Geospatial Disaster Risk Assessment**  

![Project Status](https://img.shields.io/badge/status-active-success.svg) ![Language](https://img.shields.io/badge/language-Python-blue.svg) ![Framework](https://img.shields.io/badge/framework-FastAPI-green.svg) ![Frontend](https://img.shields.io/badge/frontend-Streamlit-red.svg)

## 📌 Project Overview  
This system leverages **satellite data (NASA GPM, soil moisture)** and **machine learning models (XGBoost, Random Forest)** to provide real-time landslide and flood risk assessments for any location in India. The interactive dashboard allows users to select locations on a map and instantly visualize disaster probabilities, environmental metrics, and historical trends.

## ✨ Key Features  

### 🗺️ Interactive Analysis  
- **Click-Based Selection**: Analyze risk for any specific location in India just by clicking on the map.  
- **Real-Time Data**: Current weather integration (Temperature, Wind, Pressure, Humidity).  
- **Environmental Metrics**: Detailed insights on Rainfall (24h/72h), Soil Saturation, Slope, Elevation, and River Proximity.  

### ⚠️ Disaster Prediction  
- **Dual Risk Assessment**: Simultanous prediction of both **Landslide** and **Flood** risks.  
- **Risk Levels**: Categorized alerts (High/Medium/Low) based on probability thresholds.  
- **Historical Analysis**: View trends of risk probabilities over time to understand changing conditions.  

### 🛰️ Live Data Integration  
- **Earth Engine Integration**: Live feeds for Rainfall Radar overlays and Terrain Slope visualization.  
- **Background Refresh**: Periodic data updates via background scheduling.  

---

## 🛠️ Technology Stack  

| Component | Technology | Description |
|-----------|------------|-------------|
| **Backend** | **FastAPI** | High-performance API for model inference and data processing. |
| **Hosting** | **Uvicorn** | ASGI server for running the FastAPI application. |
| **Database** | **MongoDB (Motor)** | Async database driver for storing historical data and logs. |
| **ML Models** | **XGBoost, Scikit-learn** | Predictive models for landslide and flood probability. |
| **Geospatial** | **Google Earth Engine API** | Satellite imagery and environmental data retrieval. |
| **Frontend** | **Streamlit** | Interactive web dashboard for visualization. |
| **Mapping** | **Folium** | Leaflet-based maps for location selection and data overlay. |
| **Charts** | **Plotly** | Dynamic charts for visualizing historical trends. |
| **DevOps** | **Docker & Docker Compose** | Containerized deployment for consistent environments. |

---

## 🚀 Installation & Setup  

### Prerequisites  
- **Docker & Docker Compose** (Recommended)  
- **Google Earth Engine Service Account**: You need a `service-account.json` key file for Earth Engine access.  

### Option 1: Run with Docker (Recommended)  

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/your-repo/landslide-prediction.git
   cd landslide-prediction
   ```

2. **Configure Credentials**  
   - Place your Earth Engine `service-account.json` file inside the `backend/` directory.  
   - Alternatively, set the `EARTH_ENGINE_SERVICE_ACCOUNT` and `EARTH_ENGINE_KEY_FILE` environment variables.  

3. **Start the Application**  
   ```bash
   docker-compose up --build
   ```

4. **Access the Application**  
   - **Dashboard**: [http://localhost:8501](http://localhost:8501)  
   - **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)  

### Option 2: Manual Setup (Local Development)  

If you prefer running without Docker, follow these steps:  

#### Backend Setup  
1. Navigate to the backend directory:  
   ```bash
   cd backend
   ```
2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```
3. Run the FastAPI server:  
   ```bash
   python main.py
   ```
   *Server will start at http://localhost:8000*  

#### Frontend Setup  
1. Open a new terminal and navigate to the frontend directory:  
   ```bash
   cd frontend
   ```
2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit dashboard:  
   ```bash
   streamlit run dashboard.py
   ```
   *Dashboard will open at http://localhost:8501*  

---

## 📖 Usage Guide  

1. **Open the Dashboard**: Navigate to `http://localhost:8501`.  
2. **Select a Location**: Click anywhere on the map (default view centers on India).  
3. **View Results**: The right sidebar will populate with:  
   - **Risk Levels**: High/Medium/Low indicators for Landslide and Flood.  
   - **Detailed Metrics**: Rainfall, Soil Saturation, Slope, Elevation, etc.  
   - **Weather Info**: Current temperature, wind speed, and humidity.  
4. **Analyze Trends**: Scroll down to see historical graphs for risk probability and environmental factors.  
5. **Toggle Layers**: Use the sidebar options to show/hide Rainfall Radar overlays.  

---

## 📂 Project Structure  

```
land_slide/
├── backend/                # FastAPI application
│   ├── app/                # Main application logic
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration
│   │   ├── db/             # Database connection logic
│   │   ├── models/         # Pydantic models
│   │   └── services/       # External services (EE, Weather)
│   ├── main.py             # Entry point
│   └── requirements.txt    # Python dependencies
├── frontend/               # Streamlit dashboard
│   ├── dashboard.py        # Main dashboard script
│   └── requirements.txt    # Python dependencies
├── models/                 # ML Models directory
├── notebooks/              # Jupyter notebooks for analysis
├── docker-compose.yml      # Docker orchestration
└── README.md               # Project documentation
```

## 🤝 Contributing  
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.  

## 📄 License  
This project is licensed under the MIT License.  
