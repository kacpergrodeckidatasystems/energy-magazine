"""
BESS Data Loader Module

This module provides a clean abstraction layer for loading Battery Energy Storage
System (BESS) telemetry data from local Parquet storage into Streamlit dashboards.
It implements the Single Responsibility Principle (SRP) by isolating all data I/O
operations from the presentation layer.

Main Features:
    - Automatic discovery of available data dates
    - Unified interface for loading multiple data types
    - Error handling and logging for production reliability
    - Support for both raw telemetry and processed analytics
    - Optimized data loading with sorting and transformations

Data Types Supported:
    1. Raw Telemetry:
       - Environment data (sensors, solar, grid)
       - Inverter data (power, efficiency)
       - Battery data (voltage, current, temperature, SOC)

    2. Processed Analytics:
       - Market analytics (price recommendations)
       - Weather analytics (solar PV forecasts)

Directory Structure Expected:
    {base_dir}/
    ├── environment/
    │   ├── env_20240613.parquet
    │   └── env_20240614.parquet
    ├── inverter/
    │   ├── inv_20240613.parquet
    │   └── inv_20240614.parquet
    ├── battery/
    │   ├── bat_20240613.parquet
    │   └── bat_20240614.parquet
    └── raw/
        ├── market/
        │   └── processed/
        │       └── market_analytics.parquet
        └── weather/
            └── processed/
                └── weather_analytics.parquet

Design Benefits:
    - Separation of Concerns: Data layer independent from UI
    - Testability: Easy to mock for unit tests
    - Maintainability: Single place to update data access logic
    - Flexibility: Easy to swap storage backends

Classes:
    BESSDataLoader: Main data loading interface

Usage Example:
    >>> import streamlit as st
    >>> from data_loader import BESSDataLoader
    >>>
    >>> # Initialize loader
    >>> loader = BESSDataLoader(base_dir="./data")
    >>>
    >>> # Discover available dates
    >>> dates = loader.get_available_dates()
    >>> selected_date = st.selectbox("Select Date", dates)
    >>>
    >>> # Load daily data
    >>> df_env, df_inv, df_bat = loader.load_daily_data(selected_date)
    >>>
    >>> # Load processed analytics
    >>> df_market = loader.load_processed_file("processed/market_analytics", selected_date)

Author: BESS Operations Team
Version: 1.0.0
"""

import logging
import os

import pandas as pd

import streamlit as st

# logger: Configured logging instance for this module
# Logs data loading operations, errors, and warnings
logger = logging.getLogger(__name__)


class BESSDataLoader:
    """
    Data access layer for BESS telemetry and analytics files.

    This class handles all I/O operations for reading structured battery and
    system telemetry from local Parquet storage. It provides a clean interface
    for Streamlit dashboards to access data without dealing with file paths,
    error handling, or data transformations.

    Responsibilities:
        - Date discovery from file system
        - Loading daily telemetry datasets
        - Loading processed analytics files
        - Data sorting and optimization
        - Error handling and user feedback

    Design Pattern:
        - Repository Pattern: Abstracts data access
        - Facade Pattern: Simplifies complex file operations

    Attributes:
        base_dir (str): Root directory for all data files
        env_dir (str): Path to environment data directory
        inv_dir (str): Path to inverter data directory
        bat_dir (str): Path to battery data directory

    Thread Safety:
        - Read-only operations (thread-safe)
        - No state mutation during data loading
        - Safe for concurrent Streamlit sessions

    Performance:
        - Parquet format: Fast columnar reads
        - Sorted data: Optimized for time-series operations
        - No caching at this layer (use st.cache_data decorator)

    Example:
        >>> # Basic usage
        >>> loader = BESSDataLoader(base_dir="/data/bess/")
        >>> dates = loader.get_available_dates()
        >>> if dates:
        ...     df_env, df_inv, df_bat = loader.load_daily_data(dates[-1])
        ...     print(f"Loaded {len(df_env)} environment records")

        >>> # With error handling
        >>> try:
        ...     data = loader.load_daily_data("20240613")
        ...     if all(d is not None for d in data):
        ...         process_data(*data)
        ... except Exception as e:
        ...     logger.error(f"Failed to load data: {e}")

    Note:
        - Assumes parquet files exist and are valid
        - Returns None values on error (check before use)
        - Streamlit error messages shown to user
        - Logging captures detailed error information
    """

    def __init__(self, base_dir: str = "./data"):
        """
        Initialize BESS data loader with base directory.

        Sets up directory paths for accessing different data types. Creates
        the data access structure but does not validate existence (lazy loading).

        Args:
            base_dir (str, optional): Root directory containing data subdirectories.
                                     Default: "./data" (relative to app location)
                                     Common values:
                                     - "./data" (development)
                                     - "/opt/airflow/data" (production with Airflow)
                                     - "/mnt/data/bess" (external volume)

        Attributes Set:
            base_dir (str): Root data directory
            env_dir (str): {base_dir}/environment
            inv_dir (str): {base_dir}/inverter
            bat_dir (str): {base_dir}/battery

        Example:
            >>> # Use default relative path
            >>> loader = BESSDataLoader()
            >>>
            >>> # Use absolute path for production
            >>> loader = BESSDataLoader(base_dir="/opt/airflow/data")
            >>>
            >>> # Use environment variable
            >>> import os
            >>> data_path = os.getenv("BESS_DATA_DIR", "./data")
            >>> loader = BESSDataLoader(base_dir=data_path)

        Note:
            - Directory validation happens during data access, not initialization
            - Paths are constructed but not verified at this stage
            - Relative paths are relative to Streamlit app working directory
        """
        # base_dir: Root directory for all BESS data files
        self.base_dir = base_dir

        # env_dir: Directory path for environment sensor telemetry
        # Contains: env_{YYYYMMDD}.parquet files
        self.env_dir = os.path.join(base_dir, "environment")

        # inv_dir: Directory path for inverter performance data
        # Contains: inv_{YYYYMMDD}.parquet files
        self.inv_dir = os.path.join(base_dir, "inverter")

        # bat_dir: Directory path for battery BMS telemetry
        # Contains: bat_{YYYYMMDD}.parquet files
        self.bat_dir = os.path.join(base_dir, "battery")

    def get_available_dates(self) -> list:
        """
        Discover available data dates by scanning environment directory.

        Scans the environment data directory to find all available dates with
        telemetry data. Uses environment directory as the "source of truth"
        since it's typically populated first in the pipeline.

        Algorithm:
            1. Check if environment directory exists
            2. List all parquet files matching pattern env_*.parquet
            3. Extract date strings from filenames
            4. Sort dates chronologically (oldest to newest)

        Returns:
            list: Sorted list of date strings in YYYYMMDD format.
                 Empty list if directory doesn't exist or no files found.
                 Example: ['20240610', '20240611', '20240612', '20240613']

        Date Format:
            - Format: YYYYMMDD (8 digits, no separators)
            - Example: 20240613 = June 13, 2024
            - Sortable: Alphanumeric sorting = chronological sorting

        Example:
            >>> loader = BESSDataLoader()
            >>> dates = loader.get_available_dates()
            >>> dates
            ['20240610', '20240611', '20240612', '20240613']
            >>>
            >>> # Get most recent date
            >>> if dates:
            ...     latest = dates[-1]
            ...     print(f"Latest data: {latest}")
            Latest data: 20240613
            >>>
            >>> # Get date range
            >>> if len(dates) >= 2:
            ...     print(f"Data range: {dates[0]} to {dates[-1]}")
            Data range: 20240610 to 20240613

        Use Cases:
            - Populate date selector in Streamlit UI
            - Determine data availability before loading
            - Find latest available data
            - Calculate data coverage statistics

        Edge Cases:
            - Directory doesn't exist: Returns []
            - Directory exists but empty: Returns []
            - Malformed filenames: Silently ignored
            - Non-parquet files: Filtered out

        Performance:
            - Time: O(n log n) where n is number of files (sorting)
            - Typical: < 10ms for hundreds of files
            - No file reading, only filename scanning

        Note:
            - Assumes environment, inverter, and battery files exist for same dates
            - If dates differ, only environment dates are returned
            - For production: Consider checking all three directories
        """
        # Check if environment directory exists
        if not os.path.exists(self.env_dir):
            return []

        # List all parquet files matching pattern: env_*.parquet
        # List comprehension filters:
        # 1. Files starting with "env_"
        # 2. Files ending with ".parquet"
        files = [f for f in os.listdir(self.env_dir) if f.startswith("env_") and f.endswith(".parquet")]

        # Extract date strings from filenames and sort
        # File format: env_{YYYYMMDD}.parquet
        # Split by "_" → ['env', '{YYYYMMDD}.parquet']
        # Index [1] → '{YYYYMMDD}.parquet'
        # Split by "." → ['{YYYYMMDD}', 'parquet']
        # Index [0] → '{YYYYMMDD}'
        # sorted() → Chronological order (alphanumeric = chronological for YYYYMMDD)
        return sorted([f.split("_")[1].split(".")[0] for f in files])

    def load_daily_data(self, date_str: str) -> tuple:
        """
        Load complete daily telemetry dataset from local Parquet storage.

        Loads and sorts historical whole-day telemetry for all three BESS
        subsystems (environment, inverter, battery). Data is loaded into
        memory as pandas DataFrames, sorted by timestamp, and optimized
        for dashboard display.

        Loading Process:
            1. Load environment parquet file
            2. Load inverter parquet file
            3. Load battery parquet file
            4. Sort all DataFrames by timestamp
            5. Optimize battery module IDs (string compression)
            6. Return tuple of three DataFrames

        Args:
            date_str (str): Date string in YYYYMMDD format.
                          Example: "20240613" = June 13, 2024
                          Must match available dates from get_available_dates()

        Returns:
            tuple: (df_env, df_inv, df_bat) where:

                df_env (pd.DataFrame): Environment sensor data
                    Columns: timestamp, ambient_temp_sensor_*_C,
                            max_solar_radiation_W_m2, grid_condition_ok
                    Records: ~144 (24 hours / 10 minutes)

                df_inv (pd.DataFrame): Inverter performance data
                    Columns: timestamp, inverter_efficiency_percent,
                            active_power_output_MW, reactive_power_MVAR
                    Records: ~144

                df_bat (pd.DataFrame): Battery BMS data
                    Columns: timestamp, rack_id, battery_module_id,
                            module_voltage_V, rack_total_current_A,
                            module_temperature_C, soc_percent
                    Records: ~1440 (144 timestamps × 10 modules)

                On Error: (None, None, None)

        Raises:
            Exception: Caught internally, error message shown via st.error(),
                      and logged. Returns None tuple on any error.

        Data Transformations:
            battery_module_id optimization:
            - Before: "battery_module_01", "battery_module_02", etc.
            - After: "bat1", "bat2", etc.
            - Benefit: Shorter strings for UI display, less memory

        Example:
            >>> loader = BESSDataLoader()
            >>>
            >>> # Load specific date
            >>> df_env, df_inv, df_bat = loader.load_daily_data("20240613")
            >>>
            >>> # Check if loading succeeded
            >>> if all(d is not None for d in [df_env, df_inv, df_bat]):
            ...     print(f"Environment: {len(df_env)} records")
            ...     print(f"Inverter: {len(df_inv)} records")
            ...     print(f"Battery: {len(df_bat)} records")
            ... else:
            ...     print("Failed to load data")
            Environment: 144 records
            Inverter: 144 records
            Battery: 1440 records

            >>> # Access loaded data
            >>> df_env['timestamp'].min()
            Timestamp('2024-06-13 00:00:00')
            >>> df_env['timestamp'].max()
            Timestamp('2024-06-13 23:50:00')

            >>> # Battery module IDs are optimized
            >>> df_bat['battery_module_id'].unique()
            array(['bat1', 'bat2', 'bat3', 'bat4', 'bat5'], dtype=object)

        Error Handling:
            - FileNotFoundError: File doesn't exist for date
            - PermissionError: Insufficient read permissions
            - ParquetError: Corrupted parquet file
            - MemoryError: File too large to load

            All errors caught and handled:
            - Error displayed via st.error() in Streamlit UI
            - Detailed error logged via logger
            - Returns (None, None, None) for defensive programming

        Performance:
            - Load time: ~50-200ms for typical day (SSD)
            - Memory: ~2-5 MB for 24-hour dataset
            - Sorting: O(n log n) per DataFrame

        Use Cases:
            - Loading data for specific date in dashboard
            - Time-series analysis for single day
            - Comparison across subsystems
            - Historical data review

        Note:
            - Returns sorted DataFrames (ready for time-series plots)
            - Battery module ID optimization is in-place
            - Caller should check for None before using
            - Consider caching with st.cache_data for performance
        """
        try:
            # Load environment data and sort by timestamp
            # File: environment/env_{YYYYMMDD}.parquet
            df_env = pd.read_parquet(os.path.join(self.env_dir, f"env_{date_str}.parquet")).sort_values("timestamp")

            # Load inverter data and sort by timestamp
            # File: inverter/inv_{YYYYMMDD}.parquet
            df_inv = pd.read_parquet(os.path.join(self.inv_dir, f"inv_{date_str}.parquet")).sort_values("timestamp")

            # Load battery data and sort by timestamp
            # File: battery/bat_{YYYYMMDD}.parquet
            df_bat = pd.read_parquet(os.path.join(self.bat_dir, f"bat_{date_str}.parquet")).sort_values("timestamp")

            # Optimize battery module IDs for UI display and memory efficiency
            # Production string optimization: battery_module_01 → bat1
            # Reduces string length from 18 chars to 4-5 chars
            # Benefits: Cleaner UI, less memory, faster comparisons
            if "battery_module_id" in df_bat.columns:
                df_bat["battery_module_id"] = df_bat["battery_module_id"].str.replace("battery_module_0", "bat")

            return df_env, df_inv, df_bat

        except Exception as e:
            # Catch all exceptions to prevent dashboard crashes
            # Display user-friendly error in Streamlit UI
            st.error(f"Critical error loading tier telemetry matrix: {str(e)}")

            # Log detailed error for debugging (not shown to user)
            logger.error(f"Failed to load daily data for {date_str}: {str(e)}", exc_info=True)

            # Return None tuple so caller can detect failure
            return None, None, None

    def load_processed_file(self, file_type: str, date_str: str) -> pd.DataFrame:
        """
        Load processed analytics files from data processing pipelines.

        Loads pre-computed analytics results such as market recommendations
        or weather forecasts. These files are generated by Airflow pipelines
        and stored in the processed data directory structure.

        File Location Logic:
            Attempts to load from: {base_dir}/raw/{file_type}.parquet

            Example paths:
            - Market: data/raw/processed/market_analytics.parquet
            - Weather: data/raw/processed/weather_analytics.parquet

        Args:
            file_type (str): Type/path of processed file relative to raw directory.
                           Examples:
                           - "processed/market_analytics"
                           - "processed/weather_analytics"
                           - "market/processed/market_analytics"

            date_str (str): Date string in YYYYMMDD format.
                          Currently used for cache busting / versioning.
                          Note: Not used in path construction (files are latest)

        Returns:
            pd.DataFrame: Loaded analytics DataFrame if file exists.
                         Empty DataFrame if file not found or error occurs.

                         Market Analytics Schema:
                         - timestamp, price_eur_mwh, recommendation

                         Weather Analytics Schema:
                         - timestamp, temperature_2m, cloudcover_percent,
                           direct_radiation_w_m2, diffuse_radiation_w_m2,
                           global_radiation, estimated_power_kw

        Example:
            >>> loader = BESSDataLoader()
            >>>
            >>> # Load market analytics
            >>> df_market = loader.load_processed_file("processed/market_analytics", "20240613")
            >>> if not df_market.empty:
            ...     print(df_market['recommendation'].value_counts())
            HOLD         14
            CHARGE        5
            DISCHARGE     5

            >>> # Load weather analytics
            >>> df_weather = loader.load_processed_file("processed/weather_analytics", "20240613")
            >>> if not df_weather.empty:
            ...     print(f"Max solar power: {df_weather['estimated_power_kw'].max():.2f} kW")
            Max solar power: 68.50 kW

        File Discovery:
            - Logs file path being attempted (info level)
            - Checks file existence before loading
            - Returns empty DataFrame if not found (no exception)

        Error Handling:
            - File not found: Returns empty DataFrame (graceful degradation)
            - Read error: Exception propagates to caller
            - Malformed parquet: Exception propagates to caller

        Cache Busting:
            - date_str parameter allows cache invalidation
            - Useful with Streamlit caching: cache key includes date
            - Even though not used in path, enables version tracking

        Performance:
            - Load time: ~10-50ms for typical analytics file
            - Memory: ~50-200 KB for 24-48 hour forecast
            - No sorting applied (assumes pre-sorted)

        Use Cases:
            - Loading market price recommendations
            - Loading solar PV generation forecasts
            - Loading any pre-computed analytics
            - Dashboard data refresh

        Note:
            - Path construction may need adjustment based on deployment
            - Consider parameterizing "raw" directory in production
            - Empty DataFrame return allows graceful UI degradation
            - Logger provides debugging information

        Future Enhancement:
            - Add date-based file versioning
            - Support multiple file format backends
            - Add data validation after loading
            - Implement retry logic for transient failures
        """
        # Construct file path to processed analytics file
        # file_path: {base_dir}/raw/{file_type}.parquet
        # Matches directory structure from Airflow analytics pipelines
        file_path = os.path.join(self.base_dir, "raw", f"{file_type}.parquet")

        # Log attempted file load for debugging
        # Helps diagnose path issues and confirm data availability
        logger.info(f"Trying to load file from: {file_path}")

        # Check if file exists before attempting to load
        if os.path.exists(file_path):
            # File exists: Load and return DataFrame
            return pd.read_parquet(file_path)

        # File doesn't exist: Return empty DataFrame for graceful degradation
        # Allows UI to handle missing data without crashing
        return pd.DataFrame()
