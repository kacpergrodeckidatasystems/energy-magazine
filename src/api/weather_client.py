import logging
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Konfiguracja ścieżek
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw" / "weather"

def fetch_weather_data(lat: float = 52.11, lon: float = 20.63) -> str:
    """
    Pobiera prognozę pogody z Open-Meteo z rygorystyczną walidacją danych.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "cloudcover", "direct_radiation", "diffuse_radiation"],
        "timezone": "Europe/Warsaw",
        "forecast_days": 2
    }
    
    logger.info(f"Fetching weather forecast for: {lat}, {lon}...")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        hourly_data = data.get("hourly", {})
        if not hourly_data:
            raise ValueError("API response 'hourly' section is empty.")

        # Tworzenie DataFrame
        df = pd.DataFrame({
            'timestamp': pd.to_datetime(hourly_data.get('time', [])),
            'temperature_2m': hourly_data.get('temperature_2m', []),
            'cloudcover_percent': hourly_data.get('cloudcover', []),
            'direct_radiation_w_m2': hourly_data.get('direct_radiation', []),
            'diffuse_radiation_w_m2': hourly_data.get('diffuse_radiation', [])
        })

        # --- WALIDACJA DANYCH ---
        
        # 1. Sprawdzenie czy df nie jest pusty
        if df.empty:
            raise ValueError("Generated DataFrame is empty.")

        # 2. Sprawdzenie wymaganych kolumn
        required_cols = ['timestamp', 'temperature_2m', 'direct_radiation_w_m2']
        if not all(col in df.columns for col in required_cols):
            missing = [c for c in required_cols if c not in df.columns]
            raise ValueError(f"Missing mandatory columns: {missing}")

        # 3. Uzupełnienie braków (NaN) - zapobiega błędom w analityce
        if df.isnull().any().any():
            logger.warning("NaN values detected. Filling with interpolation.")
            df = df.interpolate(method='linear').ffill().bfill()

        # 4. Walidacja zakresów fizycznych (Logowanie ostrzeżeń dla outlierów)
        if (df['temperature_2m'] < -40).any() or (df['temperature_2m'] > 50).any():
            logger.warning("Temperature anomaly detected!")

        # --- ZAPIS ---
        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M")
        output_path = RAW_DATA_DIR / f"weather_forecast_{date_str}.parquet"
        
        df.to_parquet(output_path, index=False)
        logger.info(f"Successfully saved validated weather data to: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Pipeline failed at weather extraction: {e}")
        raise

if __name__ == "__main__":
    try:
        path = fetch_weather_data()
        print(f"Test success: {path}")
    except Exception as e:
        print(f"Test failed: {e}")