from datetime import datetime

from airflow.sdk import dag, task

# Import the new Object-Oriented Task structures and Local Storage Driver
from src.airflow.raw_to_etl import (
    BatteryIngestionTask,
    EnvironmentIngestionTask,
    InverterIngestionTask,
    LocalParquetStorage,
)


@dag(
    dag_id="bess_pure_triggers_dag",
    start_date=datetime(2026, 6, 1),
    catchup=False,
    schedule=None,
    tags=["bess", "", "aop"],
)
def bess__pipeline():

    # Initialize enterprise infrastructure components
    storage = LocalParquetStorage()
    task_env = EnvironmentIngestionTask(storage=storage)
    task_inv = InverterIngestionTask(storage=storage)
    task_bat = BatteryIngestionTask(storage=storage)

    # Setting logical_date to datetime | None = None silences Mypy
    # while allowing Airflow 3 TaskFlow engine to dynamically inject context
    @task(task_id="trigger_environment")
    def run_environment(logical_date: datetime | None = None):
        if logical_date is None:
            logical_date = datetime.now()
        target_dt = datetime(
            logical_date.year, logical_date.month, logical_date.day, logical_date.hour, logical_date.minute
        )
        return task_env.execute(target_date=target_dt)

    @task(task_id="trigger_inverter")
    def run_inverter(logical_date: datetime | None = None):
        if logical_date is None:
            logical_date = datetime.now()
        target_dt = datetime(
            logical_date.year, logical_date.month, logical_date.day, logical_date.hour, logical_date.minute
        )
        return task_inv.execute(target_date=target_dt)

    @task(task_id="trigger_batteries")
    def run_batteries(logical_date: datetime | None = None):
        if logical_date is None:
            logical_date = datetime.now()
        target_dt = datetime(
            logical_date.year, logical_date.month, logical_date.day, logical_date.hour, logical_date.minute
        )
        return task_bat.execute(target_date=target_dt)

    # Now invoking functions without arguments is fully compliant with Mypy
    env_data = run_environment()
    inv_data = run_inverter()
    bat_data = run_batteries()

    env_data >> inv_data >> bat_data


bess__pure_triggers_dag = bess__pipeline()
