"""
BESS ETL Pipeline Components Module.
Object-oriented ETL for BESS data ingestion with pluggable storage backends.
SOLID design: DataStorage, PipelineTask abstractions. Uses dependency injection.
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from src.generators.bess_telemetry_generators import (
    generate_battery_day,
    generate_environment_day,
    generate_inverter_day,
)


class BESSDataStorage(ABC):
    """
    Abstract base class for storage backends following Dependency Inversion Principle.
    Subclasses implement save_dataframe() for different storage systems (local, S3, database, etc.).
    """

    def __init__(self, base_path: str):
        """Initialize storage backend with base path."""
        self.base_path = base_path

    @abstractmethod
    def save_dataframe(self, df: pd.DataFrame, subfolder: str, filename: str) -> str:
        """Save DataFrame to storage. Returns full path/URL."""
        pass


class LocalParquetStorage(BESSDataStorage):
    """
    Local file system storage using Parquet format.
    Automatic directory creation, columnar compression, schema preservation.
    """

    def __init__(self, base_dir: str = "/opt/airflow/data/"):
        """Initialize local parquet storage."""
        self.base_dir = base_dir

    def save_dataframe(self, df: pd.DataFrame, subfolder: str, filename: str) -> str:
        """Save DataFrame to local parquet file. Returns absolute path."""
        target_dir = os.path.join(self.base_dir, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        full_path = os.path.join(target_dir, f"{filename}.parquet")
        df.to_parquet(full_path, index=False)
        return full_path


class BESSPipelineTask(ABC):
    """
    Abstract base class for ETL pipeline tasks following Template Method pattern.
    Subclasses implement execute() method to perform data generation and storage.
    Provides date resolution helper for consistent datetime handling.
    """

    def __init__(self, storage: BESSDataStorage):
        """Initialize task with storage backend (dependency injection)."""
        self.storage = storage

    @abstractmethod
    def execute(self, target_date: datetime | None = None) -> str:
        """Execute ETL task. Returns success message with path and row count."""
        pass

    def _resolve_date(self, target_date: datetime | None = None) -> datetime:
        """Resolve target date (uses current datetime if None)."""
        return target_date if target_date is not None else datetime.now()


class EnvironmentIngestionTask(BESSPipelineTask):
    """Environment telemetry ingestion (5 sensors, solar, grid). 144 records/day."""

    def execute(self, target_date: datetime | None = None) -> str:
        """Generate and save 24h environment data. Returns success message."""
        resolved_date = self._resolve_date(target_date)
        df = generate_environment_day(resolved_date)
        filename = f"env_{resolved_date.strftime('%Y%m%d')}"
        saved_path = self.storage.save_dataframe(df, "environment", filename)
        return f"Successfully ingested Environment data to {saved_path} [{len(df)} rows]"


class InverterIngestionTask(BESSPipelineTask):
    """Inverter PCS telemetry ingestion (efficiency, power). 144 records/day."""

    def execute(self, target_date: datetime | None = None) -> str:
        """Generate and save 24h inverter data. Returns success message."""
        resolved_date = self._resolve_date(target_date)
        df = generate_inverter_day(resolved_date)
        filename = f"inv_{resolved_date.strftime('%Y%m%d')}"
        saved_path = self.storage.save_dataframe(df, "inverter", filename)
        return f"Successfully ingested Inverter data to {saved_path} [{len(df)} rows]"


class BatteryIngestionTask(BESSPipelineTask):
    """Battery BMS telemetry ingestion (10 modules, 2 racks, thermal dynamics). 1440 records/day."""

    def execute(self, target_date: datetime | None = None) -> str:
        """Generate and save 24h battery data with thermal simulation. Returns success message."""
        resolved_date = self._resolve_date(target_date)
        df = generate_battery_day(resolved_date)
        filename = f"bat_{resolved_date.strftime('%Y%m%d')}"
        saved_path = self.storage.save_dataframe(df, "battery", filename)
        return f"Successfully ingested Battery data to {saved_path} [{len(df)} rows]"
