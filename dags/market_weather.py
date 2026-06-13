"""
Market & Weather Data Synchronization DAG

This Airflow DAG orchestrates the end-to-end pipeline for external data ingestion
and analytics processing for Battery Energy Storage System (BESS) operations.
It fetches real-time market prices and weather forecasts, processes them through
analytics engines, and prepares data for operational dashboards.

Pipeline Components:
    1. Data Extraction: Fetch data from external APIs
       - Market prices (currently mock data for stability)
       - Weather forecasts (Open-Meteo API)

    2. Data Transformation: Analytics processing
       - Market analytics: Generate CHARGE/DISCHARGE/HOLD recommendations
       - Weather analytics: Estimate solar PV generation capacity

    3. Data Loading: Store processed results
       - Parquet format for efficient querying
       - Accessible by Streamlit dashboards

Schedule:
    - Frequency: Every hour at 15 minutes past (e.g., 00:15, 01:15, 02:15)
    - Cron: '15 * * * *'
    - Rationale: Aligns with market price updates and weather forecast refresh cycles

Data Flow:
    market_api → market_raw.parquet → business_analytics → market_analytics.parquet
    weather_api → weather_raw.parquet → weather_analytics → weather_analytics.parquet

DAG Configuration:
    - DAG ID: bess_market_weather_sync
    - Start Date: 2026-06-01
    - Catchup: False (only process current data)
    - Retries: 2 attempts with 5-minute delay
    - Tags: ['bess', 'api', 'analytics', 'streamlit']

Dependencies:
    - src.api.market_client: Market price data fetching
    - src.api.weather_client: Weather forecast data fetching
    - src.analytics.business_logic: Market price analytics
    - src.analytics.weather_logic: Solar generation forecasting

Use Cases:
    - Real-time operational decision support
    - Battery charge/discharge optimization
    - Revenue maximization through arbitrage
    - Integration with energy management systems

Error Handling:
    - Automatic retry on API failures (2 retries, 5-min intervals)
    - Task isolation: Failures don't cascade
    - Logging for debugging and monitoring

Monitoring:
    - Airflow UI: Task status and execution times
    - Logs: Detailed operation traces
    - Alerts: Configure via Airflow alerting mechanisms

Author: BESS Operations Team
Version: 1.0.0
Last Modified: 2026-06-13
"""

from datetime import datetime, timedelta

from airflow.decorators import dag, task

from src.analytics.business_logic import process_market_analytics
from src.analytics.weather_logic import process_weather_analytics

# Import business logic modules for data pipeline
from src.api.market_client import fetch_market_data
from src.api.weather_client import fetch_weather_data

# default_args: Default configuration parameters applied to all tasks in the DAG
# These settings control retry behavior, ownership, and task dependencies
default_args = {
    "owner": "bess_admin",  # DAG owner for notifications and permissions
    "depends_on_past": False,  # Tasks can run independently of previous runs
    "retries": 2,  # Number of retry attempts on failure
    "retry_delay": timedelta(minutes=5),  # Wait time between retry attempts
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
    Market and Weather Data Pipeline orchestration function.

    This function defines the complete workflow for external data ingestion
    and processing. It uses Airflow's TaskFlow API (@task decorators) for
    clean, Pythonic DAG definition.

    Workflow Architecture:
        1. Parallel Extraction Phase:
           - get_market_data(): Fetch electricity prices
           - get_weather_data(): Fetch weather forecasts

        2. Parallel Transformation Phase:
           - analyze_business_data(): Market analytics
           - analyze_weather_data(): Solar forecasting

        3. Implicit Loading Phase:
           - Analytics functions save to parquet files
           - Streamlit dashboard reads from parquet files

    Task Dependencies:
        market_raw → business_processed
        weather_raw → weather_processed

        (No dependency between market and weather branches - parallel execution)

    Error Handling:
        - Each task has independent retry logic
        - Failures in one branch don't affect the other
        - XCom used for passing file paths between tasks

    Returns:
        None: DAG definition (no return value needed)

    Example Execution:
        # Manual trigger via CLI
        $ airflow dags trigger bess_market_weather_sync

        # Manual trigger via UI
        Navigate to DAG in Airflow UI → Trigger DAG button

    Monitoring:
        - Check task duration trends for performance degradation
        - Monitor retry rates for API reliability issues
        - Review logs for data quality warnings

    Note:
        - Tasks decorated with @task automatically handle XCom
        - Return values from tasks are passed as arguments to downstream tasks
        - All file paths use absolute paths for reliability
    """

    @task(task_id="extract_market_api")
    def get_market_data():
        """
        Fetch electricity market prices from data source.

        This task retrieves day-ahead market price data, which is essential
        for battery arbitrage optimization. Currently uses mock data generator
        for development stability, but can be switched to live ENTSO-E API.

        Data Retrieved:
            - 24-hour price forecast
            - Hourly granularity
            - EUR/MWh pricing
            - Timestamps in UTC

        Returns:
            str: Absolute file path to saved market data parquet file.
                 Format: /path/to/data/raw/market/market_prices_{timestamp}.parquet

        Raises:
            IOError: If file cannot be written
            OSError: If directory cannot be created

        Example Output:
            '/home/user/data/raw/market/market_prices_20260613_0815.parquet'

        Note:
            - Uses mock data (not live API) for development
            - For production: Replace with fetch_market_data(api_key=...)
            - Data saved in parquet format for performance

        Execution Time: ~50-100ms (mock data generation)
        Memory Usage: ~10KB (24-hour dataset)
        """
        return fetch_market_data()

    @task(task_id="extract_weather_api")
    def get_weather_data():
        """
        Fetch weather forecast data from Open-Meteo API.

        This task retrieves meteorological parameters essential for solar PV
        generation forecasting. Data includes temperature, cloud cover, and
        solar radiation components (direct and diffuse).

        Data Retrieved:
            - 48-hour forecast horizon (2 days)
            - Hourly granularity
            - Temperature at 2m height (°C)
            - Cloud cover percentage (%)
            - Direct and diffuse radiation (W/m²)

        API Details:
            - Provider: Open-Meteo (https://api.open-meteo.com)
            - Authentication: None required (free tier)
            - Timeout: 10 seconds
            - Rate limit: Typically unlimited for reasonable use

        Returns:
            str: Absolute file path to saved weather data parquet file.
                 Format: /path/to/data/raw/weather/weather_forecast_{timestamp}.parquet

        Raises:
            requests.exceptions.RequestException: If API call fails
            ValueError: If API response is invalid
            IOError: If file cannot be written

        Example Output:
            '/home/user/data/raw/weather/weather_forecast_20260613_0815.parquet'

        Data Quality:
            - Missing values interpolated
            - Physical range validation
            - Temperature anomaly detection
            - See weather_client.py for full validation logic

        Execution Time: ~200-500ms (API call + processing)
        Memory Usage: ~20KB (48-hour dataset)

        Note:
            - Live API call (not mock data)
            - Location: Warsaw, Poland (configurable)
            - Forecast updates every hour
        """
        return fetch_weather_data()

    @task(task_id="run_business_analytics")
    def analyze_business_data(market_data_path: str):
        """
        Process market prices to generate operational recommendations.

        This task transforms raw market price data into actionable battery
        management decisions using a quantile-based arbitrage strategy.

        Analytics Strategy:
            - CHARGE: During cheapest 20% of prices (bottom quintile)
            - DISCHARGE: During most expensive 20% of prices (top quintile)
            - HOLD: During mid-range prices (middle 60%)

        Input:
            market_data_path (str): Path to raw market data parquet file
                                   Expected columns: timestamp, price_eur_mwh

        Processing Steps:
            1. Load raw market prices
            2. Calculate Q1 (20th percentile) and Q4 (80th percentile)
            3. Apply recommendation logic to each price point
            4. Save enriched data with recommendations

        Output Schema:
            - timestamp: Time of price observation
            - price_eur_mwh: Electricity price
            - recommendation: 'CHARGE' | 'DISCHARGE' | 'HOLD'

        Returns:
            str: Absolute file path to processed analytics parquet file.
                 Format: /path/to/data/processed/market_analytics.parquet

        Raises:
            FileNotFoundError: If input file doesn't exist
            KeyError: If required columns missing
            IOError: If output file cannot be written

        Example Output:
            '/home/user/data/processed/market_analytics.parquet'

        Business Value:
            - Maximizes arbitrage profit
            - Reduces manual decision-making
            - Consistent strategy application
            - Historical strategy backtesting

        Execution Time: ~50ms (quantile calculation + recommendations)
        Memory Usage: ~15KB (24-hour dataset with recommendations)

        Note:
            - Strategy parameters (20%, 80%) are hardcoded
            - For production: Consider dynamic thresholds
            - Does not account for battery SOC constraints
        """
        return process_market_analytics(market_data_path)

    @task(task_id="run_weather_analytics")
    def analyze_weather_data(weather_data_path: str):
        """
        Process weather forecast to estimate solar PV generation capacity.

        This task transforms meteorological data into electrical power output
        estimates for integrated solar PV systems. Used for battery charging
        forecasts and grid interaction planning.

        Power Model:
            P = GHI × η × (1 - CC/100)

            Where:
            - P: Estimated power (kW)
            - GHI: Global Horizontal Irradiance (direct + diffuse, W/m²)
            - η: System efficiency (0.1 = 10%)
            - CC: Cloud cover (0-100%)

        Input:
            weather_data_path (str): Path to raw weather data parquet file
                                    Expected columns: timestamp, temperature_2m,
                                    direct_radiation_w_m2, diffuse_radiation_w_m2,
                                    cloudcover_percent

        Processing Steps:
            1. Load raw weather forecast
            2. Calculate global radiation (direct + diffuse)
            3. Apply power estimation model
            4. Save enriched data with power forecasts

        Output Schema:
            - All original weather columns
            - global_radiation: Total solar radiation (W/m²)
            - estimated_power_kw: PV power output estimate (kW)

        Returns:
            str: Absolute file path to processed analytics parquet file.
                 Format: /path/to/data/processed/weather_analytics.parquet

        Raises:
            FileNotFoundError: If input file doesn't exist
            KeyError: If required columns missing
            IOError: If output file cannot be written

        Example Output:
            '/home/user/data/processed/weather_analytics.parquet'

        Assumptions:
            - 100 kWp system size (implied by 0.1 efficiency factor)
            - Horizontal mounting (no tilt optimization)
            - No shading or soiling losses
            - Linear cloud cover model

        Use Cases:
            - Day-ahead charging schedule optimization
            - Grid service availability forecasting
            - Energy arbitrage planning
            - Capacity factor analysis

        Execution Time: ~50ms (radiation calculation + power model)
        Memory Usage: ~25KB (48-hour forecast with power estimates)

        Note:
            - Simplified model (not PVLib-level accuracy)
            - For production: Consider advanced models
            - Temperature derating not included
        """
        return process_weather_analytics(weather_data_path)

    # === DAG EXECUTION FLOW DEFINITION ===
    # Define task dependencies using TaskFlow API

    # Extraction Phase: Parallel data fetching
    # market_raw: File path to raw market price data
    market_raw = get_market_data()
    # weather_raw: File path to raw weather forecast data
    weather_raw = get_weather_data()

    # Transformation Phase: Parallel analytics processing
    # Analytics functions save processed data to disk for Streamlit consumption
    analyze_business_data(market_raw)
    analyze_weather_data(weather_raw)

    # Note: No explicit loading phase needed - analytics functions save to disk
    # Streamlit dashboard will read the processed parquet files directly


# === DAG INSTANTIATION ===
# Create the DAG instance by calling the decorated function
# This registers the DAG with Airflow's scheduler
pipeline_instance = bess_data_pipeline()
