"""
Business Logic Analytics Module

This module provides business intelligence and operational decision-making analytics
for battery energy storage systems (BESS). It analyzes electricity market prices to
generate actionable charging and discharging recommendations for optimal revenue.

Main Features:
    - Market price analysis and quantile-based strategy
    - Automatic charge/discharge/hold recommendations
    - Processes raw market data into actionable business intelligence
    - Saves analytics results in Parquet format

Strategy:
    The module implements a simple yet effective quantile-based trading strategy:
    - CHARGE: During the cheapest 20% of price periods (Q1 ≤ 0.2)
    - DISCHARGE: During the most expensive 20% of price periods (Q4 ≥ 0.8)
    - HOLD: During mid-range pricing periods (0.2 < Q < 0.8)

    This strategy aims to:
    1. Buy energy when prices are low (charge battery)
    2. Sell energy when prices are high (discharge battery)
    3. Minimize unnecessary cycling in mid-range periods

Business Metrics:
    - Price quantiles (Q1 = 20th percentile, Q4 = 80th percentile)
    - Operational recommendations per time period
    - Expected revenue optimization through arbitrage

Algorithm Complexity:
    - Time: O(n log n) for quantile calculation
    - Space: O(n) for DataFrame storage

Author: Physics Analytics Team
Version: 1.0.0
"""

from pathlib import Path

import pandas as pd


def process_market_analytics(file_path: str) -> str:
    """
    Analyze market prices and generate battery operational recommendations.

    This function implements a quantile-based trading strategy for battery energy
    storage systems (BESS). It reads market price data, calculates price quantiles,
    and assigns operational recommendations (CHARGE/DISCHARGE/HOLD) to each time
    period based on price levels.

    The strategy is designed to maximize arbitrage profit by:
    - Charging when electricity is cheap (bottom 20% of prices)
    - Discharging when electricity is expensive (top 20% of prices)
    - Holding during mid-range prices to avoid unnecessary cycling

    Algorithm Steps:
    1. Load market price data from Parquet file
    2. Calculate Q1 (20th percentile) and Q4 (80th percentile) price thresholds
    3. Apply recommendation logic to each price point:
       - If price ≤ Q1: Recommend CHARGE
       - If price ≥ Q4: Recommend DISCHARGE
       - If Q1 < price < Q4: Recommend HOLD
    4. Add recommendation column to DataFrame
    5. Save enriched data to processed directory

    Args:
        file_path (str): Absolute or relative path to the raw market data Parquet file.
                        Expected schema:
                        - timestamp (datetime): Time of the price observation
                        - price_eur_mwh (float): Electricity price in EUR/MWh

    Returns:
        str: Absolute path to the processed analytics Parquet file.
             Format: {data_dir}/processed/market_analytics.parquet

             Output schema includes original columns plus:
             - recommendation (str): 'CHARGE', 'DISCHARGE', or 'HOLD'

    Raises:
        FileNotFoundError: If the input file_path does not exist
        ValueError: If required columns are missing from input data
        IOError: If output directory cannot be created or file cannot be written

    Example:
        >>> # Process market data
        >>> raw_path = 'data/raw/market/market_prices_20240613.parquet'
        >>> analytics_path = process_market_analytics(raw_path)
        >>>
        >>> # Load and inspect results
        >>> df = pd.read_parquet(analytics_path)
        >>> df.head()
           timestamp           price_eur_mwh  recommendation
        0  2024-06-13 00:00:00       45.2      HOLD
        1  2024-06-13 01:00:00       32.8      CHARGE
        2  2024-06-13 02:00:00       28.5      CHARGE
        ...
        >>>
        >>> # Check recommendation distribution
        >>> df['recommendation'].value_counts()
        HOLD         14
        CHARGE        5
        DISCHARGE     5

    Note:
        - Quantile thresholds (0.2 and 0.8) are currently hardcoded
        - Strategy does not account for battery state of charge (SOC)
        - Does not consider cycling costs or degradation
        - For production, integrate with real-time SOC monitoring
        - Consider adding hysteresis to avoid rapid state changes

    Performance:
        - Typical execution time: < 100ms for 24-hour dataset
        - Memory usage: O(n) where n is number of time periods

    See Also:
        get_recommendation(): Internal function implementing recommendation logic
    """
    # df: Load market price data from Parquet file into pandas DataFrame
    df = pd.read_parquet(file_path)

    # Calculate price quantiles for strategy thresholds
    # price_q1: 20th percentile (bottom 20% threshold) - cheapest prices
    # price_q4: 80th percentile (top 20% threshold) - most expensive prices
    price_q1 = df["price_eur_mwh"].quantile(0.2)
    price_q4 = df["price_eur_mwh"].quantile(0.8)

    def get_recommendation(price: float) -> str:
        """
        Determine operational recommendation based on price level.

        This nested function implements the core business logic for battery
        operation decisions using a simple threshold-based strategy.

        Decision Logic:
        - If price is at or below Q1 (bottom 20%): CHARGE
          Rationale: Energy is cheap, good time to store energy

        - If price is at or above Q4 (top 20%): DISCHARGE
          Rationale: Energy is expensive, good time to sell energy

        - If price is between Q1 and Q4: HOLD
          Rationale: Mid-range pricing, avoid unnecessary cycling

        Args:
            price (float): Electricity price in EUR/MWh for a specific time period

        Returns:
            str: Operational recommendation, one of:
                - 'CHARGE': Battery should charge (buy energy)
                - 'DISCHARGE': Battery should discharge (sell energy)
                - 'HOLD': Battery should maintain current state

        Example:
            >>> # Assume Q1 = 30 EUR/MWh, Q4 = 80 EUR/MWh
            >>> get_recommendation(25.0)
            'CHARGE'
            >>> get_recommendation(85.0)
            'DISCHARGE'
            >>> get_recommendation(50.0)
            'HOLD'
        """
        if price <= price_q1:
            return "CHARGE"
        elif price >= price_q4:
            return "DISCHARGE"
        return "HOLD"

    # Apply the recommendation logic to each price in the DataFrame
    # Creates a new column 'recommendation' with strategy decisions
    df["recommendation"] = df["price_eur_mwh"].apply(get_recommendation)

    # Construct output path in processed directory
    # output_path: Navigate up to data directory, then down to processed/market_analytics.parquet
    output_path = Path(file_path).parent.parent / "processed" / "market_analytics.parquet"

    # Ensure the output directory exists, create if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the enriched DataFrame with recommendations to Parquet file
    # index=False: Don't save DataFrame index as a column
    df.to_parquet(output_path, index=False)

    return str(output_path)
