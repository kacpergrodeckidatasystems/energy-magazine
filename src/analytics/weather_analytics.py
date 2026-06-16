"""
Weather Analytics Module.
Solar PV power forecasting from weather data.
Model: P = GHI × 0.1 × (1 - cloudcover/100). GHI = direct + diffuse radiation.
"""

from pathlib import Path

import pandas as pd


def process_weather_analytics(file_path: str) -> str:
    """
    Estimate solar PV power from weather forecast.
    Calculates GHI (direct+diffuse), applies cloud correction.
    Returns path to processed analytics parquet file.
    """
    df = pd.read_parquet(file_path)
    df["global_radiation"] = df["direct_radiation_w_m2"] + df["diffuse_radiation_w_m2"]
    df["estimated_power_kw"] = (df["global_radiation"] * 0.1) * (1 - df["cloudcover_percent"] / 100)
    output_path = Path(file_path).parent.parent / "processed" / "weather_analytics.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    return str(output_path)
