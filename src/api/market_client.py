"""
Market Data Client Module.
Generates mock 24h electricity market prices (EUR/MWh).
Realistic patterns: morning/evening peaks, midday valley. Stores in parquet.
"""

import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw" / "market"


def _generate_mock_market_data(start_date: datetime) -> pd.DataFrame:
    """Generate 24h synthetic market prices (sinusoidal + peaks + noise). Returns DataFrame."""
    timestamps = [start_date.replace(hour=h, minute=0, second=0, microsecond=0) for h in range(24)]
    hours = np.array(range(24))
    base_price = 50 + 40 * np.sin((hours - 6) * np.pi / 12)
    peaks = 50 * np.exp(-((hours - 8) ** 2) / 2) + 60 * np.exp(-((hours - 19) ** 2) / 2)
    noise = np.random.normal(0, 5, 24)
    prices = base_price + peaks + noise
    df = pd.DataFrame({"timestamp": timestamps, "price_eur_mwh": np.maximum(prices, -20.0)})
    return df


def generate_mock_market_data() -> str:
    """
    Generate and save mock 24h market price data.
    Returns absolute file path to saved parquet file.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M")
    output_path = RAW_DATA_DIR / f"market_prices_{date_str}.parquet"
    df = _generate_mock_market_data(now)
    df.to_parquet(output_path, index=False)
    logger.info(f"Mock market data generated at: {output_path}")
    return str(output_path)
