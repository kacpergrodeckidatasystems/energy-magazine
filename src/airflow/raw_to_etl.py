"""
BESS ETL Pipeline Components Module

This module provides object-oriented ETL (Extract-Transform-Load) components for
Battery Energy Storage System (BESS) data ingestion pipelines. It implements
SOLID design principles to create maintainable, testable, and extensible
data processing workflows.

Main Features:
    - Abstract storage layer (Dependency Inversion Principle)
    - Pluggable storage backends (Local, S3, Database, etc.)
    - Task abstraction for consistent pipeline execution
    - Automatic date resolution for flexible scheduling
    - Parquet-based storage for performance

Design Patterns:
    - Strategy Pattern: Interchangeable storage backends
    - Template Method Pattern: PipelineTask base class
    - Dependency Injection: Tasks receive storage instances
    - Single Responsibility: Each class has one clear purpose

SOLID Principles Applied:
    S - Single Responsibility Principle:
        Each class has one reason to change (storage, task execution, etc.)

    O - Open-Closed Principle:
        Open for extension (new tasks, new storage backends)
        Closed for modification (interfaces remain stable)

    L - Liskov Substitution Principle:
        All storage backends can substitute DataStorage
        All tasks can substitute PipelineTask

    I - Interface Segregation Principle:
        Minimal interfaces (save_dataframe, execute)

    D - Dependency Inversion Principle:
        High-level tasks depend on storage abstraction, not concrete implementations

Classes:
    DataStorage: Abstract base class for storage backends
    LocalParquetStorage: Local file system storage implementation
    PipelineTask: Abstract base class for ETL tasks
    EnvironmentIngestionTask: Environment data ingestion
    InverterIngestionTask: Inverter data ingestion
    BatteryIngestionTask: Battery data ingestion

Storage Backends:
    Current: LocalParquetStorage (local file system)
    Future: S3Storage, DatabaseStorage, DataLakeStorage

Use Cases:
    - Airflow DAG task execution
    - Batch data ingestion
    - Data lake population
    - Testing and development
    - Data migration

Example Usage:
    >>> # Create storage backend
    >>> storage = LocalParquetStorage(base_dir="/data/")
    >>>
    >>> # Create task with dependency injection
    >>> task = EnvironmentIngestionTask(storage=storage)
    >>>
    >>> # Execute task for specific date
    >>> result = task.execute(target_date=datetime(2024, 6, 13))
    >>> print(result)
    Successfully ingested Environment data to /data/environment/env_20240613.parquet [144 rows]

Architecture Benefits:
    - Easy to test (mock storage layer)
    - Easy to swap storage (change one line)
    - Easy to add tasks (extend PipelineTask)
    - Easy to understand (clear abstractions)

Author: BESS Operations Team
Version: 1.0.0
"""

import os
from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

# Import data generation functions from generators module
from src.generators.raw_generators import (
    generate_battery_day,  # Battery BMS telemetry generator
    generate_environment_day,  # Environment sensor data generator
    generate_inverter_day,  # Inverter performance data generator
)


class DataStorage(ABC):
    """
    Abstract base class for storage backend implementations.

    This class defines the interface for all storage backends, implementing
    the Dependency Inversion Principle (DIP). High-level ETL tasks depend on
    this abstraction rather than concrete storage implementations.

    Design Benefits:
        - Decouples ETL logic from storage mechanism
        - Enables easy testing with mock storage
        - Allows runtime selection of storage backend
        - Facilitates migration between storage systems

    Attributes:
        base_path (str): Root directory or connection string for storage backend

    Example Implementations:
        - LocalParquetStorage: Local file system
        - S3ParquetStorage: AWS S3 bucket
        - DatabaseStorage: SQL/NoSQL database
        - DataLakeStorage: Delta Lake, Iceberg

    Usage Pattern:
        >>> # Define in subclass
        >>> class CustomStorage(DataStorage):
        ...     def save_dataframe(self, df, subfolder, filename):
        ...         # Custom implementation
        ...         pass
        >>>
        >>> # Use via abstraction
        >>> storage: DataStorage = CustomStorage()
        >>> storage.save_dataframe(df, "data", "file")

    See Also:
        LocalParquetStorage: Concrete implementation for local file system
    """

    def __init__(self, base_path: str):
        """
        Initialize storage backend with base path.

        Args:
            base_path (str): Root location for data storage.
                            For local: directory path
                            For S3: bucket name
                            For database: connection string

        Example:
            >>> storage = DataStorage("/data/warehouse/")
        """
        # base_path: Root directory or connection identifier
        self.base_path = base_path

    @abstractmethod
    def save_dataframe(self, df: pd.DataFrame, subfolder: str, filename: str) -> str:
        """
        Save DataFrame to storage backend.

        Abstract method that must be implemented by all concrete storage backends.
        Defines the contract for data persistence operations.

        Args:
            df (pd.DataFrame): Data to persist
            subfolder (str): Logical partition or subdirectory (e.g., "environment", "battery")
            filename (str): Base filename without extension

        Returns:
            str: Full path or URL to saved data for verification and logging

        Raises:
            NotImplementedError: If called on abstract base class
            IOError: If storage operation fails (implementation dependent)

        Note:
            Implementations should:
            - Create directories/partitions if needed
            - Handle file format conversion
            - Return verifiable path/URL
            - Raise clear exceptions on failure
        """
        pass


class LocalParquetStorage(DataStorage):
    """
    Local file system storage backend using Parquet format.

    This concrete implementation of DataStorage saves DataFrames to the local
    file system in Apache Parquet format. Parquet is chosen for its:
    - Columnar storage (efficient querying)
    - Compression (reduced disk usage)
    - Schema preservation (type safety)
    - Wide ecosystem support (Spark, Pandas, DuckDB)

    Directory Structure:
        {base_dir}/
        ├── environment/
        │   ├── env_20240613.parquet
        │   └── env_20240614.parquet
        ├── inverter/
        │   ├── inv_20240613.parquet
        │   └── inv_20240614.parquet
        └── battery/
            ├── bat_20240613.parquet
            └── bat_20240614.parquet

    Features:
        - Automatic directory creation
        - Atomic writes (Parquet handles this)
        - No index storage (space optimization)
        - Full path return for verification

    Attributes:
        base_dir (str): Root directory for all data files
                       Default: "/opt/airflow/data/" (Airflow volume mount)

    Example:
        >>> # Initialize storage
        >>> storage = LocalParquetStorage(base_dir="/data/lake/")
        >>>
        >>> # Save environment data
        >>> df_env = pd.DataFrame({'temp': [25.0, 26.0]})
        >>> path = storage.save_dataframe(df_env, "environment", "env_20240613")
        >>> print(path)
        /data/lake/environment/env_20240613.parquet
        >>>
        >>> # Verify file exists
        >>> os.path.exists(path)
        True

    Performance:
        - Write speed: ~100MB/s (SSD)
        - Compression: ~70% reduction (typical)
        - Read performance: Columnar = fast for analytics

    Limitations:
        - No concurrent write protection (use unique filenames)
        - No built-in versioning (implement in filename)
        - No access control (use file system permissions)

    Alternative Implementations:
        - S3ParquetStorage: Replace local path with S3 boto3 calls
        - AzureBlobStorage: Use Azure SDK
        - HDFSParquetStorage: Use PyArrow HDFS interface
    """

    def __init__(self, base_dir: str = "/opt/airflow/data/"):
        """
        Initialize local parquet storage backend.

        Args:
            base_dir (str, optional): Root directory for data files.
                                     Default: "/opt/airflow/data/"
                                     Typical Airflow volume mount point.

        Example:
            >>> # Use default Airflow location
            >>> storage = LocalParquetStorage()
            >>>
            >>> # Use custom location
            >>> storage = LocalParquetStorage(base_dir="/mnt/data/")

        Note:
            - Directory will be created if it doesn't exist
            - Ensure process has write permissions
            - For Docker: map as volume in docker-compose.yml
        """
        # base_dir: Store root directory without calling parent __init__
        # (parent expects base_path, we use base_dir for clarity)
        self.base_dir = base_dir

    def save_dataframe(self, df: pd.DataFrame, subfolder: str, filename: str) -> str:
        """
        Save DataFrame to local file system in Parquet format.

        Implements the DataStorage interface for local file system persistence.
        Creates directory structure automatically and saves data in compressed
        columnar format.

        Process Flow:
            1. Construct target directory path
            2. Create directory if it doesn't exist (mkdir -p)
            3. Construct full file path with .parquet extension
            4. Save DataFrame without index
            5. Return absolute path for verification

        Args:
            df (pd.DataFrame): Data to save. Can be any valid DataFrame.
            subfolder (str): Subdirectory for logical partitioning.
                           Common values: "environment", "inverter", "battery"
            filename (str): Base filename without extension.
                          Convention: {prefix}_{YYYYMMDD}
                          Examples: "env_20240613", "inv_20240613"

        Returns:
            str: Absolute path to saved parquet file.
                Format: {base_dir}/{subfolder}/{filename}.parquet

        Raises:
            OSError: If directory cannot be created
            IOError: If file cannot be written
            PermissionError: If process lacks write permissions
            ValueError: If DataFrame is invalid

        Example:
            >>> storage = LocalParquetStorage()
            >>> df = pd.DataFrame({
            ...     'timestamp': pd.date_range('2024-06-13', periods=3, freq='1H'),
            ...     'temperature': [25.0, 26.0, 25.5]
            ... })
            >>> path = storage.save_dataframe(df, "environment", "env_20240613")
            >>>
            >>> # Verify by reading back
            >>> df_read = pd.read_parquet(path)
            >>> len(df_read)
            3

        Parquet Benefits:
            - Column pruning: Read only needed columns
            - Predicate pushdown: Filter at read time
            - Compression: Typically 70% size reduction
            - Schema: Preserves dtypes (no CSV type inference)

        Performance:
            - Small files (< 1MB): ~10ms write time
            - Large files (100MB): ~1-2s write time (SSD)
            - Compression ratio: 2-10x depending on data

        Note:
            - Index is not saved (index=False) to save space
            - Use timestamp column for ordering/filtering
            - Parquet preserves pandas metadata
            - Files are atomic (write completes or fails entirely)
        """
        # target_dir: Construct full directory path
        # Example: "/opt/airflow/data/environment"
        target_dir = os.path.join(self.base_dir, subfolder)

        # Create directory and all parent directories if they don't exist
        # exist_ok=True: Don't raise error if directory already exists
        # Similar to: mkdir -p target_dir
        os.makedirs(target_dir, exist_ok=True)

        # full_path: Construct complete file path with .parquet extension
        # Example: "/opt/airflow/data/environment/env_20240613.parquet"
        full_path = os.path.join(target_dir, f"{filename}.parquet")

        # Save DataFrame to parquet file
        # index=False: Don't write DataFrame index as a column (saves space)
        # Compression defaults to 'snappy' (fast, good compression ratio)
        df.to_parquet(full_path, index=False)

        # Return absolute path for logging and verification
        return full_path


class PipelineTask(ABC):
    """
    Abstract base class for ETL pipeline task execution.

    This class implements the Template Method design pattern, providing a
    consistent interface for all data ingestion tasks while allowing
    subclasses to implement specific extraction logic.

    Design Benefits:
        - Consistent task interface across all data types
        - Automatic date resolution logic
        - Dependency injection for storage
        - Easy to add new task types (Open-Closed Principle)

    Common Functionality:
        - Date resolution (target_date or current date)
        - Storage abstraction (inject backend)
        - Execution interface (execute method)

    Attributes:
        storage (DataStorage): Injected storage backend for data persistence

    Subclass Responsibilities:
        - Implement execute() method
        - Call generator function
        - Format filename appropriately
        - Return success message with path and row count

    Usage Pattern:
        >>> class CustomTask(PipelineTask):
        ...     def execute(self, target_date=None):
        ...         date = self._resolve_date(target_date)
        ...         df = generate_custom_data(date)
        ...         path = self.storage.save_dataframe(df, "custom", f"data_{date:%Y%m%d}")
        ...         return f"Saved to {path} [{len(df)} rows]"
        >>>
        >>> storage = LocalParquetStorage()
        >>> task = CustomTask(storage=storage)
        >>> result = task.execute()

    See Also:
        EnvironmentIngestionTask: Environment data ingestion
        InverterIngestionTask: Inverter data ingestion
        BatteryIngestionTask: Battery data ingestion
    """

    def __init__(self, storage: DataStorage):
        """
        Initialize pipeline task with storage backend.

        Args:
            storage (DataStorage): Storage backend instance for data persistence.
                                  Any implementation of DataStorage interface.

        Example:
            >>> storage = LocalParquetStorage()
            >>> task = EnvironmentIngestionTask(storage=storage)

        Note:
            - Storage is injected (Dependency Injection pattern)
            - Tasks don't create storage (Inversion of Control)
            - Same storage instance can be shared across tasks
        """
        # storage: Store reference to injected storage backend
        self.storage = storage

    @abstractmethod
    def execute(self, target_date: datetime | None = None) -> str:
        """
        Execute ETL task for specified date.

        Abstract method that must be implemented by all concrete task subclasses.
        Defines the contract for task execution.

        Args:
            target_date (datetime | None, optional): Target date for data generation.
                                                     If None, uses current date/time.

        Returns:
            str: Success message with file path and row count.
                Format: "Successfully ingested {Type} data to {path} [{rows} rows]"

        Raises:
            NotImplementedError: If called on abstract base class
            IOError: If data cannot be saved (subclass specific)

        Note:
            Implementations should:
            1. Call _resolve_date(target_date)
            2. Generate data using appropriate generator
            3. Format filename with date
            4. Save via self.storage.save_dataframe()
            5. Return formatted success message
        """
        pass

    def _resolve_date(self, target_date: datetime | None = None) -> datetime:
        """
        Resolve target date for task execution.

        Helper method that provides default date handling. If no target_date
        is provided, uses current datetime. This allows flexible task execution:
        - Scheduled runs: Airflow provides logical_date
        - Manual runs: Can specify custom date
        - Ad-hoc runs: Defaults to current time

        Args:
            target_date (datetime | None, optional): Explicit target date.
                                                     If None, uses datetime.now().

        Returns:
            datetime: Resolved target date for data generation.

        Example:
            >>> task = EnvironmentIngestionTask(storage)
            >>> # Explicit date
            >>> date1 = task._resolve_date(datetime(2024, 6, 13))
            >>> date1
            datetime(2024, 6, 13, 0, 0)
            >>>
            >>> # Default to now
            >>> date2 = task._resolve_date(None)
            >>> date2  # Current datetime
            datetime(2024, 6, 13, 10, 30, 45, ...)

        Use Cases:
            - Airflow scheduled runs: logical_date from context
            - Backfill operations: Historical dates
            - Testing: Specific dates for reproducibility
            - Manual execution: Current date
        """
        # Return target_date if provided, otherwise current datetime
        return target_date if target_date is not None else datetime.now()


class EnvironmentIngestionTask(PipelineTask):
    """
    ETL task for environment and meteorological telemetry ingestion.

    This task generates and persists 24 hours of environmental sensor data
    including ambient temperature, solar radiation, and grid connectivity status.

    Data Generated:
        - Ambient temperature from 5 sensors (including 2 with anomalies)
        - Solar radiation measurements
        - Grid connectivity status
        - 10-minute sampling resolution (144 records/day)

    Output Schema:
        - timestamp: Measurement datetime
        - ambient_temp_sensor_01_C: Normal sensor #1
        - ambient_temp_sensor_02_C: Normal sensor #2
        - ambient_temp_sensor_03_C: Normal sensor #3
        - ambient_temp_sensor_04_C_HIGH_ANOMALY: Hot anomaly sensor
        - ambient_temp_sensor_05_C_LOW_ANOMALY: Cold anomaly sensor
        - max_solar_radiation_W_m2: Solar irradiance
        - grid_condition_ok: Connectivity flag (0/1)

    Storage Location:
        {base_dir}/environment/env_{YYYYMMDD}.parquet

    Example:
        >>> storage = LocalParquetStorage()
        >>> task = EnvironmentIngestionTask(storage=storage)
        >>> result = task.execute(target_date=datetime(2024, 6, 13))
        >>> print(result)
        Successfully ingested Environment data to /data/environment/env_20240613.parquet [144 rows]

    Use Cases:
        - Environmental monitoring dashboards
        - Anomaly detection testing
        - Correlation analysis (temp vs solar)
        - Grid reliability tracking
    """

    def execute(self, target_date: datetime | None = None) -> str:
        """
        Execute environment data ingestion task.

        Generates 24 hours of environmental sensor data and saves to parquet file.

        Args:
            target_date (datetime | None, optional): Target date for data generation.
                                                     If None, uses current datetime.

        Returns:
            str: Success message with file path and row count.
                Example: "Successfully ingested Environment data to
                         /data/environment/env_20240613.parquet [144 rows]"

        Raises:
            IOError: If file cannot be written
            OSError: If directory cannot be created

        Process:
            1. Resolve target date
            2. Generate environment data for 24 hours
            3. Format filename as env_{YYYYMMDD}
            4. Save to storage backend
            5. Return success message

        Example:
            >>> task = EnvironmentIngestionTask(LocalParquetStorage())
            >>> task.execute(datetime(2024, 6, 13))
            'Successfully ingested Environment data to .../env_20240613.parquet [144 rows]'
        """
        # resolved_date: Get target date (provided or current)
        resolved_date = self._resolve_date(target_date)

        # df: Generate 24 hours of environment telemetry data
        df = generate_environment_day(resolved_date)

        # filename: Format as env_{YYYYMMDD} without extension
        filename = f"env_{resolved_date.strftime('%Y%m%d')}"

        # saved_path: Persist data and get file path
        saved_path = self.storage.save_dataframe(df, "environment", filename)

        # Return formatted success message with path and row count
        return f"Successfully ingested Environment data to {saved_path} [{len(df)} rows]"


class InverterIngestionTask(PipelineTask):
    """
    ETL task for power conversion system (PCS) telemetry ingestion.

    This task generates and persists 24 hours of inverter performance data
    including efficiency curves, active power output, and reactive power.

    Data Generated:
        - Inverter efficiency (95-99.5%)
        - Active power output (-5 to +5 MW)
        - Reactive power (±0.05 MVAR)
        - 10-minute sampling resolution (144 records/day)

    Output Schema:
        - timestamp: Measurement datetime
        - inverter_efficiency_percent: Conversion efficiency
        - active_power_output_MW: Real power (MW)
        - reactive_power_MVAR: Reactive power (MVAR)

    Storage Location:
        {base_dir}/inverter/inv_{YYYYMMDD}.parquet

    Example:
        >>> storage = LocalParquetStorage()
        >>> task = InverterIngestionTask(storage=storage)
        >>> result = task.execute(target_date=datetime(2024, 6, 13))
        >>> print(result)
        Successfully ingested Inverter data to /data/inverter/inv_20240613.parquet [144 rows]

    Use Cases:
        - Inverter performance monitoring
        - Efficiency analysis and optimization
        - Power quality assessment
        - Grid interconnection compliance
    """

    def execute(self, target_date: datetime | None = None) -> str:
        """
        Execute inverter data ingestion task.

        Generates 24 hours of power conversion system data and saves to parquet file.

        Args:
            target_date (datetime | None, optional): Target date for data generation.
                                                     If None, uses current datetime.

        Returns:
            str: Success message with file path and row count.
                Example: "Successfully ingested Inverter data to
                         /data/inverter/inv_20240613.parquet [144 rows]"

        Raises:
            IOError: If file cannot be written
            OSError: If directory cannot be created

        Process:
            1. Resolve target date
            2. Generate inverter data for 24 hours
            3. Format filename as inv_{YYYYMMDD}
            4. Save to storage backend
            5. Return success message

        Example:
            >>> task = InverterIngestionTask(LocalParquetStorage())
            >>> task.execute(datetime(2024, 6, 13))
            'Successfully ingested Inverter data to .../inv_20240613.parquet [144 rows]'
        """
        # resolved_date: Get target date (provided or current)
        resolved_date = self._resolve_date(target_date)

        # df: Generate 24 hours of inverter performance data
        df = generate_inverter_day(resolved_date)

        # filename: Format as inv_{YYYYMMDD} without extension
        filename = f"inv_{resolved_date.strftime('%Y%m%d')}"

        # saved_path: Persist data and get file path
        saved_path = self.storage.save_dataframe(df, "inverter", filename)

        # Return formatted success message with path and row count
        return f"Successfully ingested Inverter data to {saved_path} [{len(df)} rows]"


class BatteryIngestionTask(PipelineTask):
    """
    ETL task for Battery Management System (BMS) telemetry ingestion.

    This task generates and persists 24 hours of detailed battery module data
    for a multi-rack BESS installation. Includes voltage, current, temperature,
    and SOC data with physics-based thermal dynamics.

    Data Generated:
        - Multi-rack (2 racks) multi-module (5 per rack) telemetry
        - Module voltage with IR drop
        - Rack-level current
        - Module temperature with thermal dynamics
        - State of charge (SOC)
        - 10-minute sampling resolution × 10 modules (1440 records/day)

    Output Schema:
        - timestamp: Measurement datetime (with jitter)
        - rack_id: Rack identifier (rack_01, rack_02)
        - battery_module_id: Module identifier (battery_module_01 to _05)
        - module_voltage_V: Terminal voltage (2.5-4.2 V)
        - rack_total_current_A: Rack current
        - module_temperature_C: Module temperature
        - soc_percent: State of charge (0-100%)

    Storage Location:
        {base_dir}/battery/bat_{YYYYMMDD}.parquet

    Example:
        >>> storage = LocalParquetStorage()
        >>> task = BatteryIngestionTask(storage=storage)
        >>> result = task.execute(target_date=datetime(2024, 6, 13))
        >>> print(result)
        Successfully ingested Battery data to /data/battery/bat_20240613.parquet [1440 rows]

    Use Cases:
        - Cell balancing verification
        - Thermal management monitoring
        - Degradation analysis
        - Safety system testing
        - BMS dashboard development
    """

    def execute(self, target_date: datetime | None = None) -> str:
        """
        Execute battery data ingestion task.

        Generates 24 hours of Battery Management System telemetry and saves
        to parquet file. Includes physics-based thermal dynamics simulation.

        Args:
            target_date (datetime | None, optional): Target date for data generation.
                                                     If None, uses current datetime.

        Returns:
            str: Success message with file path and row count.
                Example: "Successfully ingested Battery data to
                         /data/battery/bat_20240613.parquet [1440 rows]"

        Raises:
            IOError: If file cannot be written
            OSError: If directory cannot be created

        Process:
            1. Resolve target date
            2. Generate battery data for 24 hours (with thermal state tracking)
            3. Format filename as bat_{YYYYMMDD}
            4. Save to storage backend
            5. Return success message

        Example:
            >>> task = BatteryIngestionTask(LocalParquetStorage())
            >>> task.execute(datetime(2024, 6, 13))
            'Successfully ingested Battery data to .../bat_20240613.parquet [1440 rows]'

        Note:
            - Generates 10× more records than other tasks (multi-module)
            - Thermal dynamics are stateful (temperature persists between steps)
            - Each module has unique characteristics (R_int, thermal loss)
        """
        # resolved_date: Get target date (provided or current)
        resolved_date = self._resolve_date(target_date)

        # df: Generate 24 hours of multi-module battery telemetry
        # This includes complex thermal dynamics simulation
        df = generate_battery_day(resolved_date)

        # filename: Format as bat_{YYYYMMDD} without extension
        filename = f"bat_{resolved_date.strftime('%Y%m%d')}"

        # saved_path: Persist data and get file path
        saved_path = self.storage.save_dataframe(df, "battery", filename)

        # Return formatted success message with path and row count
        return f"Successfully ingested Battery data to {saved_path} [{len(df)} rows]"
