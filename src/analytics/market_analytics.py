"""
Business Logic Analytics Module.
Market price analysis with quantile-based BESS charging strategy.
CHARGE (Q1≤0.2), DISCHARGE (Q4≥0.8), HOLD (mid-range).
"""

from pathlib import Path

import pandas as pd


def process_market_analytics(file_path: str) -> str:
    """
    Generate BESS operational recommendations from market prices.
    Uses quantile strategy: CHARGE (≤Q1=20%), DISCHARGE (≥Q4=80%), HOLD (mid).
    Returns path to processed analytics parquet file.
    """
    df = pd.read_parquet(file_path)
    low_price_threshold_q1 = df["price_eur_mwh"].quantile(0.2)
    high_price_threshold_q4 = df["price_eur_mwh"].quantile(0.8)

    def get_recommendation(price: float) -> str:
        """Determine recommendation based on price quantile."""
        if price <= low_price_threshold_q1:
            return "CHARGE"
        elif price >= high_price_threshold_q4:
            return "DISCHARGE"
        return "HOLD"

    df["recommendation"] = df["price_eur_mwh"].apply(get_recommendation)
    output_path = Path(file_path).parent.parent / "processed" / "market_analytics.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    return str(output_path)
