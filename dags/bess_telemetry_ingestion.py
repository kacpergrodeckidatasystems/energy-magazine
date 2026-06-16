"""
BESS Telemetry Data Ingestion DAG

"""

from datetime import datetime

from airflow.sdk import dag, task

from src.airflow.bess_etl_pipeline import (
    BatteryIngestionTask,  # Battery BMS data generation task
    EnvironmentIngestionTask,  # Environmental sensor data generation task
    InverterIngestionTask,  # Power conversion system data generation task
    LocalParquetStorage,  # Local file system storage adapter
)


@dag(
    dag_id="bess_telemetry_ingestion",  # Unique identifier for this DAG
    start_date=datetime(2026, 6, 1),  # DAG activation date
    catchup=False,  # Don't backfill historical runs
    schedule=None,  # Manual trigger only (no automatic schedule)
    tags=["bess", "telemetry", "ingestion"],  # Tags for filtering and organization
)
def bess_telemetry_pipeline():
    """
    BESS data pipeline orchestration function for synthetic telemetry generation.

    """
    storage = LocalParquetStorage()

    task_environment = EnvironmentIngestionTask(storage=storage)

    task_inverter = InverterIngestionTask(storage=storage)

    task_battery = BatteryIngestionTask(storage=storage)

    @task(task_id="trigger_environment")
    def run_environment(target_date: datetime | None = None):
        """
        Generate and store environment telemetry data for the target date.

        """
        if target_date is None:
            target_date = datetime.now()

        target_dt = datetime(target_date.year, target_date.month, target_date.day, target_date.hour, target_date.minute)

        return task_environment.execute(target_date=target_dt)

    @task(task_id="trigger_inverter")
    def run_inverter(target_date: datetime | None = None):
        """
        Generate and store inverter telemetry data for the target date.

        """
        if target_date is None:
            target_date = datetime.now()

        target_dt = datetime(target_date.year, target_date.month, target_date.day, target_date.hour, target_date.minute)

        return task_inverter.execute(target_date=target_dt)

    @task(task_id="trigger_batteries")
    def run_batteries(target_date: datetime | None = None):
        """
        Generate and store battery telemetry data for the target date.

        """
        if target_date is None:
            target_date = datetime.now()

        target_dt = datetime(target_date.year, target_date.month, target_date.day, target_date.hour, target_date.minute)

        return task_battery.execute(target_date=target_dt)

    environment_data = run_environment()

    inverter_data = run_inverter()

    battery_data = run_batteries()

    environment_data >> inverter_data >> battery_data


bess_telemetry_dag = bess_telemetry_pipeline()
