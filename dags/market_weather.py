"""
BESS Market & Weather Data Synchronization DAG.
Fetches market prices and weather forecasts, runs analytics, saves to parquet.
Schedule: Every hour at 15 minutes past. Tags: bess, api, analytics, streamlit.
"""

from datetime import datetime, timedelta

from airflow.decorators import dag, task

from src.analytics.market_analytics import process_market_analytics
from src.analytics.weather_analytics import process_weather_analytics

# Import business logic modules for data pipeline
from src.api.market_client import generate_mock_market_data
from src.api.weather_client import fetch_weather_data

default_args = {
    "owner": "bess_admin",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="bess_market_weather_sync",  # Unique identifier for the DAG
    default_args=default_args,  # Apply default arguments to all tasks
    description="BESS Pipeline: Fetch API Data -> Run Analytics -> Refresh Streamlit Dashboard",
    schedule="15 * * * *",  # Cron expression: Run at 15 minutes past every hour
    start_date=datetime(2026, 6, 1),  # DAG becomes active from this date
    catchup=False,  # Don't backfill historical runs
    tags=["bess", "api", "analytics", "streamlit"],  # Tags for filtering in UI
)
def bess_data_pipeline():
    """
    BESS data pipeline orchestration function.
    Parallel extraction (market, weather) → Parallel analytics → Save to parquet.
    """

    @task(task_id="extract_market_api")
    def get_market_data():
        """
        Generate mock electricity market prices (24h forecast, hourly, EUR/MWh).
        Returns absolute file path to saved parquet file.
        """
        return generate_mock_market_data()

    @task(task_id="extract_weather_api")
    def get_weather_data():
        """
        Fetch weather forecast from Open-Meteo API (48h, temp, clouds, radiation).
        Returns absolute file path to saved parquet file.
        """
        return fetch_weather_data()

    @task(task_id="run_business_analytics")
    def analyze_business_data(market_data_path: str):
        """
        Process market prices, generate CHARGE/DISCHARGE/HOLD recommendations.
        Uses quantile-based strategy (Q1=20%, Q4=80%).
        """
        return process_market_analytics(market_data_path)

    @task(task_id="run_weather_analytics")
    def analyze_weather_data(weather_data_path: str):
        """
        Estimate solar PV power from weather data.
        Model: P = GHI × 0.1 × (1 - cloudcover/100).
        """
        return process_weather_analytics(weather_data_path)

    market_data = get_market_data()
    weather_data = get_weather_data()
    analyze_business_data(market_data)
    analyze_weather_data(weather_data)


pipeline_instance = bess_data_pipeline()
