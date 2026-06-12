import os
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw" / "market"


def _generate_mock_market_data(start_date: datetime) -> pd.DataFrame:
    """
    Generates realistic synthetic market prices:
    - 24-hour cycle (24 entries, hourly)
    - Price peaks: 08:00 and 19:00
    - Price valleys: 03:00 and 14:00 (PV production peak)
    """
    # Create 24 hours of timestamps
    timestamps = [start_date.replace(hour=h, minute=0, second=0, microsecond=0) for h in range(24)]
    
    # Generate base prices with some noise
    # Sinusoidal baseline to simulate day/night cycles
    hours = np.array(range(24))
    base_price = 50 + 40 * np.sin((hours - 6) * np.pi / 12)  # Lows around 14:00, Highs around 02:00?
    
    # Adjust to reflect actual grid demand patterns
    # Add peaks at 8am and 7pm
    peaks = 50 * np.exp(-((hours - 8)**2) / 2) + 60 * np.exp(-((hours - 19)**2) / 2)
    
    # Add random noise
    noise = np.random.normal(0, 5, 24)
    
    prices = base_price + peaks + noise
    
    df = pd.DataFrame({
        "timestamp": timestamps,
        "price_eur_mwh": np.maximum(prices, -20.0) # Ensure prices don't drop below -20 EUR
    })
    
    return df

def fetch_market_data() -> str:
    """
    Always returns path to mock market data. 
    Skipping live ENTSO-E API for development stability.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M")
    output_path = RAW_DATA_DIR / f"market_prices_{date_str}.parquet"

    # ZAWSZE generuj mock, nie szukaj klucza w środowisku
    df = _generate_mock_market_data(now)

    df.to_parquet(output_path, index=False)
    logger.info(f"Mock market data generated at: {output_path}")
    
    return str(output_path)