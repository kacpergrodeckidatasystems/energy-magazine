import os
from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from src.generators.raw_generators import generate_battery_day, generate_environment_day, generate_inverter_day


class DataStorage(ABC):
    """Abstract base class to isolate I/O operations (Dependency Inversion Principle)"""

    def __init__(self, base_path: str):
        self.base_path = base_path

    @abstractmethod
    def save_dataframe(self, df: pd.DataFrame, subfolder: str, filename: str) -> str:
        pass


class LocalParquetStorage(DataStorage):
    """Handles writing DataFrames into local Parquet structure (SRP)"""

    def __init__(self, base_dir: str = "/opt/airflow/data/"):
        self.base_dir = base_dir

    def save_dataframe(self, df: pd.DataFrame, subfolder: str, filename: str) -> str:
        target_dir = os.path.join(self.base_dir, subfolder)
        os.makedirs(target_dir, exist_ok=True)

        full_path = os.path.join(target_dir, f"{filename}.parquet")
        df.to_parquet(full_path, index=False)
        return full_path


class PipelineTask(ABC):
    """Abstract Layer for dynamic ETL pipeline execution (Open-Closed Principle)"""

    def __init__(self, storage: DataStorage):
        self.storage = storage

    @abstractmethod
    def execute(self, target_date: datetime | None = None) -> str:  # <-- Updated type hint
        pass

    def _resolve_date(self, target_date: datetime | None = None) -> datetime:  # <-- Updated type hint
        return target_date if target_date is not None else datetime.now()


class EnvironmentIngestionTask(PipelineTask):
    """Ingests whole-day meteorological and ambient telemetry"""

    def execute(self, target_date: datetime | None = None) -> str:  # <-- Updated type hint
        resolved_date = self._resolve_date(target_date)
        df = generate_environment_day(resolved_date)

        filename = f"env_{resolved_date.strftime('%Y%m%d')}"
        saved_path = self.storage.save_dataframe(df, "environment", filename)
        return f"Successfully ingested Environment data to {saved_path} [{len(df)} rows]"


class InverterIngestionTask(PipelineTask):
    """Ingests whole-day PCS power conversion and efficiency matrix"""

    def execute(self, target_date: datetime | None = None) -> str:  # <-- Updated type hint
        resolved_date = self._resolve_date(target_date)
        df = generate_inverter_day(resolved_date)

        filename = f"inv_{resolved_date.strftime('%Y%m%d')}"
        saved_path = self.storage.save_dataframe(df, "inverter", filename)
        return f"Successfully ingested Inverter data to {saved_path} [{len(df)} rows]"


class BatteryIngestionTask(PipelineTask):
    """Ingests whole-day BMS multi-rack submodule telemetry"""

    def execute(self, target_date: datetime | None = None) -> str:  # <-- Updated type hint
        resolved_date = self._resolve_date(target_date)
        df = generate_battery_day(resolved_date)

        filename = f"bat_{resolved_date.strftime('%Y%m%d')}"
        saved_path = self.storage.save_dataframe(df, "battery", filename)
        return f"Successfully ingested Battery data to {saved_path} [{len(df)} rows]"
