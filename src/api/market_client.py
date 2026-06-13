"""
Market Data Client Module

This module provides functionality for fetching electricity market price data.
It generates mock market data that simulates realistic day-ahead electricity
pricing patterns for development and testing purposes.

Main Features:
    - Generates 24-hour synthetic market price data
    - Simulates realistic price patterns with morning and evening peaks
    - Stores data in Parquet format for efficient processing
    - Configured for European market pricing patterns (EUR/MWh)

Data Characteristics:
    - Morning peak: ~08:00 (work start)
    - Evening peak: ~19:00 (residential demand)
    - Valley periods: ~03:00 and ~14:00 (PV production peak)
    - Price range: -20 to ~150 EUR/MWh

Constants:
    BASE_DIR (Path): Root directory of the project
    RAW_DATA_DIR (Path): Directory path for storing raw market data files
    logger (Logger): Configured logging instance for this module

Author: Physics Analytics Team
Version: 1.0.0
"""

import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# Configure logging for market data operations
# Logs include timestamp, severity level, and message for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# BASE_DIR: Root directory of the project (parent of parent of parent of this file)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# RAW_DATA_DIR: Storage location for raw market price data in Parquet format
RAW_DATA_DIR = BASE_DIR / "data" / "raw" / "market"


def _generate_mock_market_data(start_date: datetime) -> pd.DataFrame:
    """
    Generate realistic synthetic electricity market price data for 24 hours.

    This internal function creates mock day-ahead market prices that simulate
    actual European electricity market behavior with characteristic patterns:
    - Morning consumption peak around 08:00 (industrial/commercial start)
    - Evening consumption peak around 19:00 (residential demand)
    - Low prices during midday (solar PV generation peak)
    - Night valley around 03:00 (minimal consumption)

    The generation uses:
    - Sinusoidal baseline for natural day/night cycle
    - Gaussian peaks for demand surges
    - Random noise for realistic price volatility

    Args:
        start_date (datetime): Starting date and time for the 24-hour period.
                              The hour component will be normalized to create
                              hourly data points from 00:00 to 23:00.

    Returns:
        pd.DataFrame: DataFrame with columns:
            - timestamp (datetime): Hourly timestamps for 24 hours
            - price_eur_mwh (float): Electricity price in EUR per MWh
                                    Range: -20 to ~150 EUR/MWh

    Example:
        >>> start = datetime(2024, 6, 13, 10, 30)  # Any time on June 13
        >>> df = _generate_mock_market_data(start)
        >>> len(df)
        24
        >>> df.columns.tolist()
        ['timestamp', 'price_eur_mwh']
        >>> df['timestamp'].iloc[0].hour
        0  # Always starts at midnight

    Note:
        This is an internal function (prefixed with _) and should not be
        called directly from outside this module. Use fetch_market_data() instead.
    """
    # Create 24 hours of timestamps, starting from midnight of the given date
    # All timestamps are normalized to the top of each hour (minute=0, second=0)
    timestamps = [start_date.replace(hour=h, minute=0, second=0, microsecond=0) for h in range(24)]

    # Generate base prices with sinusoidal pattern to simulate daily cycle
    # hours: Array [0, 1, 2, ..., 23] representing each hour of the day
    hours = np.array(range(24))

    # base_price: Sinusoidal pattern with 50 EUR baseline and 40 EUR amplitude
    # Shifted by 6 hours to have natural lows around 14:00 (solar peak)
    base_price = 50 + 40 * np.sin((hours - 6) * np.pi / 12)

    # Add characteristic consumption peaks using Gaussian distributions
    # peaks: Sharp price increases during high-demand periods
    # Morning peak (8am): 50 EUR amplitude with std dev = sqrt(2)
    # Evening peak (7pm): 60 EUR amplitude with std dev = sqrt(2)
    peaks = 50 * np.exp(-((hours - 8) ** 2) / 2) + 60 * np.exp(-((hours - 19) ** 2) / 2)

    # noise: Random price volatility with normal distribution
    # Mean = 0, Standard deviation = 5 EUR for realistic market fluctuations
    noise = np.random.normal(0, 5, 24)

    # prices: Combined signal = baseline + demand peaks + random volatility
    prices = base_price + peaks + noise

    # Create DataFrame with timestamp and price columns
    # np.maximum ensures prices don't drop below -20 EUR (negative prices can occur
    # in real markets during oversupply, but are constrained to realistic ranges)
    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "price_eur_mwh": np.maximum(prices, -20.0),  # Floor at -20 EUR/MWh
        }
    )

    return df


def fetch_market_data() -> str:
    """
    Fetch and save electricity market price data for the current day.

    This is the main entry point for obtaining market data. Currently configured
    to generate mock data for development stability instead of calling live APIs
    (e.g., ENTSO-E Transparency Platform). The function creates a 24-hour price
    forecast and saves it in Parquet format with a timestamp in the filename.

    The function performs the following operations:
    1. Creates the raw data directory if it doesn't exist
    2. Generates a timestamp for the current execution
    3. Creates synthetic market data for 24 hours
    4. Saves the data to a Parquet file with timestamped filename
    5. Logs the operation and returns the file path

    Returns:
        str: Absolute file path to the saved Parquet file containing market data.
             Format: {RAW_DATA_DIR}/market_prices_{YYYYMMDD_HHMM}.parquet

    Raises:
        OSError: If the data directory cannot be created
        IOError: If the Parquet file cannot be written

    Example:
        >>> path = fetch_market_data()
        >>> print(path)
        /home/user/projects/physics/data/raw/market/market_prices_20240613_1430.parquet
        >>> df = pd.read_parquet(path)
        >>> df.shape
        (24, 2)

    Note:
        - The function always generates mock data (not calling live ENTSO-E API)
        - For production, replace _generate_mock_market_data() with actual API call
        - Data is saved in Parquet format for performance and compression benefits
        - Filename includes execution timestamp to prevent overwrites

    See Also:
        _generate_mock_market_data(): Internal function generating the mock data
    """
    # Ensure the raw data directory exists, create parent directories if needed
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Get current timestamp for filename and as start date for data generation
    now = datetime.now()

    # date_str: Formatted timestamp for unique filename (YYYYMMDD_HHMM)
    date_str = now.strftime("%Y%m%d_%H%M")

    # output_path: Full path where the market data will be saved
    output_path = RAW_DATA_DIR / f"market_prices_{date_str}.parquet"

    # Generate mock market data for development/testing
    # TODO: Replace with actual ENTSO-E API call for production deployment
    df = _generate_mock_market_data(now)

    # Save DataFrame to Parquet file (compressed columnar format)
    # index=False: Don't save the DataFrame index as a column
    df.to_parquet(output_path, index=False)

    # Log successful data generation for monitoring and debugging
    logger.info(f"Mock market data generated at: {output_path}")

    return str(output_path)
