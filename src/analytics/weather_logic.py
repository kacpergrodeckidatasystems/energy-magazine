import pandas as pd
from pathlib import Path

def process_weather_analytics(file_path: str) -> str:
    """
    Calculates estimated solar power generation based on weather forecast.
    
    Returns:
        str: Path to the processed weather analytics parquet file.
    """
    df = pd.read_parquet(file_path)
    
    # Basic model: Power (W) is roughly proportional to global radiation
    # Assuming a simplified 100kWp system efficiency
    df['global_radiation'] = df['direct_radiation_w_m2'] + df['diffuse_radiation_w_m2']
    df['estimated_power_kw'] = (df['global_radiation'] * 0.1) * (1 - df['cloudcover_percent'] / 100)
    
    output_path = Path(file_path).parent.parent / "processed" / "weather_analytics.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    return str(output_path)