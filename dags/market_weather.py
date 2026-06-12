from datetime import datetime, timedelta
from airflow.decorators import dag, task

# Import business logic modules
from src.api.market_client import fetch_market_data
from src.api.weather_client import fetch_weather_data
from src.analytics.business_logic import process_market_analytics
from src.analytics.weather_logic import process_weather_analytics

# Default arguments for the DAG
default_args = {
    'owner': 'bess_admin',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='bess_market_weather_sync',
    default_args=default_args,
    description='BESS Pipeline: Fetch API Data -> Run Analytics -> Refresh Streamlit Dashboard',
    schedule='15 * * * *',  
    start_date=datetime(2026, 6, 1),
    catchup=False,
    tags=['bess', 'api', 'analytics', 'streamlit'],
)
def bess_data_pipeline():

    @task(task_id='extract_market_api')
    def get_market_data():
        return fetch_market_data()

    @task(task_id='extract_weather_api')
    def get_weather_data():
        return fetch_weather_data()

    @task(task_id='run_business_analytics')
    def analyze_business_data(market_data_path: str):
        return process_market_analytics(market_data_path)

    @task(task_id='run_weather_analytics')
    def analyze_weather_data(weather_data_path: str):
        return process_weather_analytics(weather_data_path)

    
    # Execution flow
    market_raw = get_market_data()
    weather_raw = get_weather_data()

    business_processed = analyze_business_data(market_raw)
    weather_processed = analyze_weather_data(weather_raw)

# Instantiate the DAG
pipeline_instance = bess_data_pipeline()