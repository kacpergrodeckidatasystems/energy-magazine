"""
Weather Data Client Module.
Fetches weather forecast from Open-Meteo API (temp, clouds, radiation, 48h).
Data validation, interpolation, parquet storage. Default: Warsaw, Poland.
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw" / "weather"


def fetch_weather_data(latitude: float = 52.11, longitude: float = 20.63) -> str:
    """
    Fetch 48h weather forecast from Open-Meteo API with validation.
    Interpolates missing values, validates temp range. Returns file path to saved parquet.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "cloudcover", "direct_radiation", "diffuse_radiation"],
        "timezone": "Europe/Warsaw",
        "forecast_days": 2,
    }
    logger.info(f"Fetching weather forecast for: {latitude}, {longitude}...")

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        hourly_data = data.get("hourly", {})
        if not hourly_data:
            raise ValueError("API response 'hourly' section is empty.")

        df = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(hourly_data.get("time", [])),
                "temperature_2m": hourly_data.get("temperature_2m", []),
                "cloudcover_percent": hourly_data.get("cloudcover", []),
                "direct_radiation_w_m2": hourly_data.get("direct_radiation", []),
                "diffuse_radiation_w_m2": hourly_data.get("diffuse_radiation", []),
            }
        )

        if df.empty:
            raise ValueError("Generated DataFrame is empty.")
        required_cols = ["timestamp", "temperature_2m", "direct_radiation_w_m2"]
        if not all(col in df.columns for col in required_cols):
            missing = [c for c in required_cols if c not in df.columns]
            raise ValueError(f"Missing mandatory columns: {missing}")
        if df.isnull().any().any():
            logger.warning("NaN values detected. Filling with interpolation.")
            df = df.interpolate(method="linear").ffill().bfill()
        if (df["temperature_2m"] < -40).any() or (df["temperature_2m"] > 50).any():
            logger.warning("Temperature anomaly detected!")

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
    """Test execution for standalone module testing."""
    try:
        path = fetch_weather_data()
        print(f"Test success: {path}")
    except Exception as e:
        print(f"Test failed: {e}")
