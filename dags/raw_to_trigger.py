"""
BESS Telemetry Data Ingestion DAG

This Airflow DAG orchestrates the generation and storage of synthetic Battery
Energy Storage System (BESS) telemetry data. It creates realistic time-series
data for three core subsystems: environment sensors, power conversion system
(inverter), and battery management system (BMS).

Pipeline Purpose:
    Generate realistic BESS operational data for:
    - Development and testing without hardware
    - Dashboard demonstration and training
    - Algorithm validation and backtesting
    - Machine learning dataset creation
    - System integration testing

Data Subsystems Generated:
    1. Environment Telemetry:
       - Ambient temperature sensors (with anomalies)
       - Solar radiation measurements
       - Grid connectivity status

    2. Inverter Telemetry:
       - Power conversion efficiency
       - Active power output (MW)
       - Reactive power (MVAR)

    3. Battery Telemetry:
       - Multi-rack voltage and current
       - Module-level temperature
       - State of charge (SOC)

Architecture:
    This DAG follows SOLID design principles:
    - Dependency Inversion Principle (DIP): Uses storage abstraction
    - Single Responsibility: Each task handles one subsystem
    - Open-Closed: Easy to add new subsystems or storage backends

Schedule:
    - Trigger: Manual (schedule=None)
    - Catchup: False (don't backfill)
    - Rationale: On-demand data generation for testing/development

Task Execution Flow:
    run_environment() → run_inverter() → run_batteries()

    Sequential execution ensures:
    - Resource management (prevent parallel file writes)
    - Logical ordering (environment → power systems → batteries)
    - Debugging simplicity (clear execution path)

Storage Backend:
    LocalParquetStorage - Stores data in parquet format
    - Location: data/raw/{subsystem}/
    - Format: Parquet (columnar, compressed)
    - Partitioning: By date and subsystem

Dependencies:
    - src.airflow.raw_to_etl: Task classes and storage abstraction
    - src.generators.raw_generators: Data generation engines

Use Cases:
    - Continuous integration testing
    - Dashboard UI/UX development
    - Analytics algorithm development
    - Training and demonstrations
    - Load testing and performance benchmarking

Error Handling:
    - Tasks fail independently (no cascading failures)
    - Logs capture generation details
    - File paths returned for verification

Monitoring:
    - Check generated file sizes for consistency
    - Validate data schemas post-generation
    - Monitor generation times for performance

Design Pattern:
    - Strategy Pattern: Interchangeable storage backends
    - Factory Pattern: Task creation with dependency injection
    - Template Method: Consistent task execution interface

Author: BESS Operations Team
Version: 1.0.0
Last Modified: 2026-06-13
"""

from datetime import datetime

from airflow.sdk import dag, task

# Import Object-Oriented Task structures and Local Storage Driver
# These classes follow Dependency Inversion Principle (DIP)
from src.airflow.raw_to_etl import (
    BatteryIngestionTask,  # Battery BMS data generation task
    EnvironmentIngestionTask,  # Environmental sensor data generation task
    InverterIngestionTask,  # Power conversion system data generation task
    LocalParquetStorage,  # Local file system storage adapter
)


@dag(
    dag_id="bess_pure_triggers_dag",  # Unique identifier for this DAG
    start_date=datetime(2026, 6, 1),  # DAG activation date
    catchup=False,  # Don't backfill historical runs
    schedule=None,  # Manual trigger only (no automatic schedule)
    tags=["bess", "telemetry", "ingestion"],  # Tags for filtering and organization
)
def bess__pipeline():
    """
    BESS data pipeline orchestration function for synthetic telemetry generation.

    This function defines the complete workflow for generating realistic BESS
    operational data across three subsystems. It uses object-oriented task
    design with dependency injection for clean separation of concerns.

    Architecture Benefits:
        1. Dependency Injection: Storage backend passed to tasks
           - Easy to swap LocalParquetStorage for S3, database, etc.
           - Tasks don't depend on storage implementation

        2. Task Isolation: Each task is self-contained
           - Independent failure modes
           - Clear responsibilities
           - Easy to test and debug

        3. Sequential Execution: Ordered task chain
           - Prevents resource contention
           - Logical data flow
           - Simplified dependency management

    Task Execution Order:
        1. run_environment(): Generate environment sensor data
           - Ambient temperature (5 sensors, 2 with anomalies)
           - Solar radiation measurements
           - Grid connectivity status
           - Output: ~144 records for 24 hours (10-min sampling)

        2. run_inverter(): Generate inverter performance data
           - Power conversion efficiency
           - Active/reactive power
           - Output: ~144 records for 24 hours

        3. run_batteries(): Generate battery BMS data
           - Multi-rack and multi-module telemetry
           - Voltage, current, temperature, SOC
           - Output: ~1440 records (144 timestamps × 10 modules)

    Data Generation:
        All data is deterministic with controlled randomness:
        - Physics-based profiles ensure realistic patterns
        - Noise added for realism
        - Anomalies injected for monitoring system testing

    Storage:
        LocalParquetStorage handles file operations:
        - Creates directory structure automatically
        - Saves data in efficient parquet format
        - Returns file paths for downstream verification

    Error Handling:
        - Each task can fail independently
        - Task failures logged with full context
        - Storage errors bubble up with clear messages

    Returns:
        None: DAG definition (no return value)

    Example Usage:
        # Manual trigger via Airflow CLI
        $ airflow dags trigger bess_pure_triggers_dag

        # Trigger with specific logical date
        $ airflow dags trigger bess_pure_triggers_dag \
          --conf '{"logical_date": "2024-06-13T00:00:00"}'

        # Trigger via Airflow UI
        Navigate to DAG → Trigger DAG button → Set parameters

    Monitoring:
        - Task Duration: Should be consistent (~100-500ms per task)
        - File Sizes: Should match expected record counts
        - Data Quality: Run validation queries on generated files

    Extensibility:
        To add new subsystem:
        1. Create new task class in raw_to_etl.py
        2. Add task instantiation here
        3. Add task function with @task decorator
        4. Add to dependency chain

        Example:
        ```python
        task_new = NewSubsystemTask(storage=storage)

        @task(task_id="trigger_new_subsystem")
        def run_new_subsystem(logical_date: datetime | None = None):
            if logical_date is None:
                logical_date = datetime.now()
            target_dt = datetime(logical_date.year, ...)
            return task_new.execute(target_date=target_dt)

        # Add to chain
        bat_data >> run_new_subsystem()
        ```

    Note:
        - Logical date defaults to current time if not provided
        - All subsystems use same target date for consistency
        - File paths returned via XCom for downstream tasks
    """

    # === STORAGE INITIALIZATION ===
    # storage: Create local parquet storage adapter
    # This instance is shared across all tasks for consistency
    # Alternative: Could inject different storage backends (S3, Database, etc.)
    storage = LocalParquetStorage()

    # === TASK INITIALIZATION ===
    # Create task instances with dependency injection
    # Each task is configured with the same storage backend

    # task_env: Environment sensor data generation task
    task_env = EnvironmentIngestionTask(storage=storage)

    # task_inv: Inverter performance data generation task
    task_inv = InverterIngestionTask(storage=storage)

    # task_bat: Battery BMS telemetry generation task
    task_bat = BatteryIngestionTask(storage=storage)

    @task(task_id="trigger_environment")
    def run_environment(logical_date: datetime | None = None):
        """
        Generate and store environment telemetry data for the target date.

        This task creates 24 hours of environmental sensor readings including
        ambient temperature, solar radiation, and grid connectivity status.
        Data includes intentional anomalies for monitoring system testing.

        Process Flow:
            1. Determine target date (use logical_date or current time)
            2. Normalize to specific datetime (preserve hour/minute)
            3. Execute environment data generation
            4. Store in parquet format via storage adapter
            5. Return file path for verification

        Args:
            logical_date (datetime | None): Target date for data generation.
                                           If None, uses current datetime.
                                           Typically provided by Airflow scheduler.

        Returns:
            str: File path to generated environment data parquet file.
                Format: data/raw/environment/environment_{YYYYMMDD_HHMM}.parquet

        Data Generated:
            - Records: ~144 (24 hours / 10 minutes)
            - Columns: 8 (timestamp + 5 temp sensors + solar + grid)
            - Size: ~10-15 KB

        Anomalies Included:
            - Sensor 4: High temperature bias (+8.2°C)
            - Sensor 5: Constant low reading (-6.5°C)

        Execution Time: ~100-200ms
        Memory Usage: ~50KB peak

        Example Output Path:
            'data/raw/environment/environment_20260613_0830.parquet'

        Note:
            - Preserves hour and minute from logical_date
            - Uses physics-based profile for realistic patterns
            - Gaussian noise added for sensor variability
        """
        # Determine target datetime
        if logical_date is None:
            logical_date = datetime.now()

        # target_dt: Normalized datetime preserving hour and minute
        # Ensures consistent data generation for scheduled runs
        target_dt = datetime(
            logical_date.year, logical_date.month, logical_date.day, logical_date.hour, logical_date.minute
        )

        # Execute task and return file path
        return task_env.execute(target_date=target_dt)

    @task(task_id="trigger_inverter")
    def run_inverter(logical_date: datetime | None = None):
        """
        Generate and store inverter telemetry data for the target date.

        This task creates 24 hours of power conversion system (PCS) performance
        data including efficiency curves, active power output, and reactive
        power measurements.

        Process Flow:
            1. Determine target date (use logical_date or current time)
            2. Normalize to specific datetime (preserve hour/minute)
            3. Execute inverter data generation
            4. Store in parquet format via storage adapter
            5. Return file path for verification

        Args:
            logical_date (datetime | None): Target date for data generation.
                                           If None, uses current datetime.
                                           Typically provided by Airflow scheduler.

        Returns:
            str: File path to generated inverter data parquet file.
                Format: data/raw/inverter/inverter_{YYYYMMDD_HHMM}.parquet

        Data Generated:
            - Records: ~144 (24 hours / 10 minutes)
            - Columns: 4 (timestamp + efficiency + active_power + reactive_power)
            - Size: ~8-12 KB

        Power Characteristics:
            - Range: -5 to +5 MW (bidirectional)
            - Efficiency: 95-99.5% (U-shaped curve)
            - Reactive power: Minimal (±0.05 MVAR)

        Execution Time: ~100-200ms
        Memory Usage: ~50KB peak

        Example Output Path:
            'data/raw/inverter/inverter_20260613_0830.parquet'

        Note:
            - Efficiency decreases at low and high power loads
            - Power follows charge/discharge patterns from physics profile
            - Noise added for realistic measurement variation
        """
        # Determine target datetime
        if logical_date is None:
            logical_date = datetime.now()

        # target_dt: Normalized datetime preserving hour and minute
        target_dt = datetime(
            logical_date.year, logical_date.month, logical_date.day, logical_date.hour, logical_date.minute
        )

        # Execute task and return file path
        return task_inv.execute(target_date=target_dt)

    @task(task_id="trigger_batteries")
    def run_batteries(logical_date: datetime | None = None):
        """
        Generate and store battery telemetry data for the target date.

        This task creates 24 hours of detailed Battery Management System (BMS)
        telemetry including multi-rack voltage, current, temperature, and state
        of charge data. Generates data for 10 modules across 2 racks with
        physics-based thermal dynamics.

        Process Flow:
            1. Determine target date (use logical_date or current time)
            2. Normalize to specific datetime (preserve hour/minute)
            3. Execute battery data generation with thermal state tracking
            4. Store in parquet format via storage adapter
            5. Return file path for verification

        Args:
            logical_date (datetime | None): Target date for data generation.
                                           If None, uses current datetime.
                                           Typically provided by Airflow scheduler.

        Returns:
            str: File path to generated battery data parquet file.
                Format: data/raw/battery/battery_{YYYYMMDD_HHMM}.parquet

        Data Generated:
            - Records: ~1440 (144 timestamps × 10 modules)
            - Columns: 7 (timestamp + rack_id + module_id + voltage +
                        current + temperature + SOC)
            - Size: ~50-80 KB

        System Configuration:
            - Racks: 2 (rack_01, rack_02)
            - Modules per rack: 5 (battery_module_01 to _05)
            - Total measurement points: 10

        Physical Models:
            - Voltage: OCV(SOC) - I×R_int
            - Temperature: Thermal dynamics with I²R heating
            - SOC: Module-specific offsets from trend
            - Current: Slight rack imbalance (96-100%)

        Execution Time: ~300-500ms (more complex due to thermal state)
        Memory Usage: ~100KB peak

        Example Output Path:
            'data/raw/battery/battery_20260613_0830.parquet'

        Note:
            - Thermal state persists between time steps (stateful)
            - Each module has unique characteristics (R_int, thermal loss)
            - Timestamp jitter (±5s) simulates asynchronous sampling
            - Data suitable for thermal anomaly detection testing
        """
        # Determine target datetime
        if logical_date is None:
            logical_date = datetime.now()

        # target_dt: Normalized datetime preserving hour and minute
        target_dt = datetime(
            logical_date.year, logical_date.month, logical_date.day, logical_date.hour, logical_date.minute
        )

        # Execute task and return file path
        return task_bat.execute(target_date=target_dt)

    # === DAG EXECUTION FLOW ===
    # Define task execution and dependencies

    # Execute tasks and capture file paths via XCom
    # env_data: File path to environment telemetry
    env_data = run_environment()

    # inv_data: File path to inverter telemetry
    inv_data = run_inverter()

    # bat_data: File path to battery telemetry
    bat_data = run_batteries()

    # Define sequential dependencies using >> operator
    # This ensures: environment → inverter → batteries
    # Rationale:
    # - Prevents parallel file I/O contention
    # - Logical ordering (environment affects systems)
    # - Simplified debugging (clear execution path)
    env_data >> inv_data >> bat_data


# === DAG INSTANTIATION ===
# Create the DAG instance by calling the decorated function
# This registers the DAG with Airflow's scheduler
bess__pure_triggers_dag = bess__pipeline()
