import pandas as pd
from pathlib import Path

def process_market_analytics(file_path: str) -> str:
    """
    Analyzes market prices to generate operational recommendations.
    
    Returns:
        str: Path to the processed analytics parquet file.
    """
    df = pd.read_parquet(file_path)
    
    # Simple strategy: Charge during the cheapest 20%, Discharge during the most expensive 20%
    price_q1 = df['price_eur_mwh'].quantile(0.2)
    price_q4 = df['price_eur_mwh'].quantile(0.8)
    
    def get_recommendation(price):
        if price <= price_q1:
            return 'CHARGE'
        elif price >= price_q4:
            return 'DISCHARGE'
        return 'HOLD'
    
    df['recommendation'] = df['price_eur_mwh'].apply(get_recommendation)
    
    output_path = Path(file_path).parent.parent / "processed" / "market_analytics.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    
    return str(output_path)