"""
Weather Data Client Module

This module provides functionality for fetching weather forecast data from the
Open-Meteo API. It retrieves hourly weather parameters essential for solar PV
energy production forecasting and battery system optimization.

Main Features:
    - Fetches real-time weather forecasts from Open-Meteo API
    - Retrieves temperature, cloud cover, and solar radiation data
    - Performs comprehensive data validation and quality checks
    - Handles missing values through interpolation
    - Stores data in Parquet format for efficient processing

Weather Parameters Retrieved:
    - Temperature at 2m height (°C)
    - Cloud cover percentage (%)
    - Direct solar radiation (W/m²)
    - Diffuse solar radiation (W/m²)

Data Quality Assurance:
    - Validates API response structure
    - Checks for required columns
    - Interpolates missing values (NaN)
    - Validates physical ranges for temperature
    - Logs warnings for data anomalies

Constants:
    BASE_DIR (Path): Root directory of the project
    RAW_DATA_DIR (Path): Directory path for storing raw weather data files
    logger (Logger): Configured logging instance for this module

Default Location:
    Warsaw, Poland (lat: 52.11, lon: 20.63)

API Used:
    Open-Meteo (https://api.open-meteo.com)
    - Free, open-source weather API
    - No authentication required
    - Hourly forecast data
    - 2-day forecast horizon

Author: Physics Analytics Team
Version: 1.0.0
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

# Configure logging for weather data operations
# Logs include timestamp, severity level, and message for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# BASE_DIR: Root directory of the project (parent of parent of parent of this file)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# RAW_DATA_DIR: Storage location for raw weather forecast data in Parquet format
RAW_DATA_DIR = BASE_DIR / "data" / "raw" / "weather"


def fetch_weather_data(lat: float = 52.11, lon: float = 20.63) -> str:
    """
    Fetch weather forecast data from Open-Meteo API with comprehensive validation.

    This function retrieves a 2-day hourly weather forecast from the Open-Meteo API,
    focusing on parameters critical for solar PV energy production modeling:
    temperature, cloud cover, direct and diffuse solar radiation.

    The function performs extensive data quality checks including:
    - API response validation
    - Schema verification (required columns)
    - Missing value detection and interpolation
    - Physical range validation for temperature
    - Data completeness verification

    Data Flow:
    1. Create data directory if needed
    2. Send HTTP GET request to Open-Meteo API
    3. Parse JSON response
    4. Create pandas DataFrame from hourly data
    5. Validate data structure and content
    6. Interpolate missing values
    7. Check physical constraints
    8. Save to timestamped Parquet file
    9. Return file path for downstream processing

    Args:
        lat (float, optional): Latitude coordinate for weather forecast location.
                              Default: 52.11 (Warsaw, Poland)
                              Valid range: -90 to +90 degrees
        lon (float, optional): Longitude coordinate for weather forecast location.
                              Default: 20.63 (Warsaw, Poland)
                              Valid range: -180 to +180 degrees

    Returns:
        str: Absolute file path to the saved Parquet file containing weather forecast.
             Format: {RAW_DATA_DIR}/weather_forecast_{YYYYMMDD_HHMM}.parquet

             DataFrame schema:
             - timestamp (datetime64): Hourly timestamps
             - temperature_2m (float): Temperature at 2m height in °C
             - cloudcover_percent (float): Cloud cover percentage (0-100)
             - direct_radiation_w_m2 (float): Direct solar radiation in W/m²
             - diffuse_radiation_w_m2 (float): Diffuse solar radiation in W/m²

    Raises:
        requests.exceptions.RequestException: If API request fails (network, timeout, HTTP error)
        ValueError: If API response is invalid or empty
                   If required columns are missing from the response
                   If DataFrame is unexpectedly empty
        IOError: If Parquet file cannot be written
        OSError: If data directory cannot be created

    Example:
        >>> # Fetch weather for Warsaw (default)
        >>> path = fetch_weather_data()
        >>> df = pd.read_parquet(path)
        >>> df.columns.tolist()
        ['timestamp', 'temperature_2m', 'cloudcover_percent',
         'direct_radiation_w_m2', 'diffuse_radiation_w_m2']

        >>> # Fetch weather for custom location (Berlin)
        >>> path_berlin = fetch_weather_data(lat=52.52, lon=13.41)
        >>> df_berlin = pd.read_parquet(path_berlin)
        >>> len(df_berlin)  # 2 days * 24 hours
        48

    Note:
        - API timeout is set to 10 seconds
        - Missing values (NaN) are interpolated using linear method
        - Temperature range check: logs warning if outside [-40°C, +50°C]
        - Timezone is hardcoded to 'Europe/Warsaw'
        - Forecast horizon is 2 days (48 hours)

    See Also:
        Open-Meteo API documentation: https://open-meteo.com/en/docs
    """
    # Ensure the raw data directory exists, create parent directories if needed
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # API endpoint URL for Open-Meteo forecast service
    url = "https://api.open-meteo.com/v1/forecast"

    # params: Dictionary of query parameters for the API request
    params = {
        "latitude": lat,  # Latitude coordinate
        "longitude": lon,  # Longitude coordinate
        "hourly": [  # List of hourly variables to retrieve
            "temperature_2m",  # Temperature at 2 meters height (°C)
            "cloudcover",  # Total cloud cover (%)
            "direct_radiation",  # Direct solar radiation (W/m²)
            "diffuse_radiation",  # Diffuse solar radiation (W/m²)
        ],
        "timezone": "Europe/Warsaw",  # Timezone for timestamp localization
        "forecast_days": 2,  # Number of forecast days (48 hours)
    }

    # Log the fetch operation for monitoring and debugging
    logger.info(f"Fetching weather forecast for: {lat}, {lon}...")

    try:
        # Send GET request to Open-Meteo API with 10-second timeout
        response = requests.get(url, params=params, timeout=10)

        # Raise HTTPError for bad responses (4xx, 5xx status codes)
        response.raise_for_status()

        # Parse JSON response into Python dictionary
        data = response.json()

        # Extract hourly forecast data from response
        # hourly_data: Dictionary containing arrays for each weather parameter
        hourly_data = data.get("hourly", {})

        # Validate that hourly data section exists and is not empty
        if not hourly_data:
            raise ValueError("API response 'hourly' section is empty.")

        # Create DataFrame from hourly data arrays
        # Each parameter is extracted with .get() to handle missing keys gracefully
        df = pd.DataFrame(
            {
                # timestamp: Convert ISO 8601 time strings to pandas datetime objects
                "timestamp": pd.to_datetime(hourly_data.get("time", [])),
                # temperature_2m: Temperature at 2m height in degrees Celsius
                "temperature_2m": hourly_data.get("temperature_2m", []),
                # cloudcover_percent: Total cloud cover as percentage (0-100%)
                "cloudcover_percent": hourly_data.get("cloudcover", []),
                # direct_radiation_w_m2: Direct (beam) solar radiation intensity
                "direct_radiation_w_m2": hourly_data.get("direct_radiation", []),
                # diffuse_radiation_w_m2: Diffuse (scattered) solar radiation intensity
                "diffuse_radiation_w_m2": hourly_data.get("diffuse_radiation", []),
            }
        )

        # === DATA VALIDATION SECTION ===
        # Comprehensive quality checks to ensure data integrity

        # Validation 1: Check if DataFrame is not empty
        if df.empty:
            raise ValueError("Generated DataFrame is empty.")

        # Validation 2: Check for required columns
        # required_cols: Minimum columns needed for downstream analytics
        required_cols = ["timestamp", "temperature_2m", "direct_radiation_w_m2"]
        if not all(col in df.columns for col in required_cols):
            # Identify which required columns are missing
            missing = [c for c in required_cols if c not in df.columns]
            raise ValueError(f"Missing mandatory columns: {missing}")

        # Validation 3: Fill missing values (NaN) to prevent errors in analytics
        if df.isnull().any().any():
            # Log warning about missing data detection
            logger.warning("NaN values detected. Filling with interpolation.")

            # Interpolate missing values using multiple methods:
            # 1. interpolate(method='linear'): Linear interpolation between valid points
            # 2. ffill(): Forward fill for leading NaNs
            # 3. bfill(): Backward fill for trailing NaNs
            df = df.interpolate(method="linear").ffill().bfill()

        # Validation 4: Validate physical ranges (log warnings for outliers)
        # Temperature sanity check: realistic range is -40°C to +50°C
        if (df["temperature_2m"] < -40).any() or (df["temperature_2m"] > 50).any():
            logger.warning("Temperature anomaly detected!")

        # === SAVE DATA SECTION ===

        # Get current timestamp for filename generation
        now = datetime.now()

        # date_str: Formatted timestamp for unique filename (YYYYMMDD_HHMM)
        date_str = now.strftime("%Y%m%d_%H%M")

        # output_path: Full path where the weather data will be saved
        output_path = RAW_DATA_DIR / f"weather_forecast_{date_str}.parquet"

        # Save DataFrame to Parquet file (compressed columnar format)
        # index=False: Don't save the DataFrame index as a column
        df.to_parquet(output_path, index=False)

        # Log successful data fetch and save operation
        logger.info(f"Successfully saved validated weather data to: {output_path}")

        return str(output_path)

    except Exception as e:
        # Catch all exceptions and log with context
        # Re-raise to allow caller to handle the error
        logger.error(f"Pipeline failed at weather extraction: {e}")
        raise


# === MODULE EXECUTION SECTION ===
# This block runs only when the script is executed directly (not imported)
if __name__ == "__main__":
    """
    Test execution block for standalone module testing.

    Executes a test fetch of weather data using default parameters (Warsaw)
    and reports success or failure. Useful for development and debugging.
    """
    try:
        # Attempt to fetch weather data
        path = fetch_weather_data()
        print(f"Test success: {path}")
    except Exception as e:
        # Print error message if fetch fails
        print(f"Test failed: {e}")
