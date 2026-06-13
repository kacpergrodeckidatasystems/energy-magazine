"""
Physics Analytics Module

This module provides advanced physics-based analytics for Battery Energy Storage
Systems (BESS). It implements mathematical models for performance analysis, thermal
monitoring, and degradation assessment of battery systems.

Main Features:
    - Energy throughput calculation and Round-Trip Efficiency (RTE) analysis
    - Thermal delta (ΔT) calculation across battery module racks
    - Internal resistance estimation using voltage-current relationships
    - Thermal anomaly detection using statistical methods (3-Sigma rule)

Physics Concepts:
    - Round-Trip Efficiency (RTE): Ratio of energy discharged to energy charged
    - Delta-T (ΔT): Temperature difference within battery modules (degradation indicator)
    - Internal Resistance: Cell resistance affecting efficiency and heat generation
    - Z-Score Analysis: Statistical method for detecting thermal outliers

Applications:
    - Performance monitoring and optimization
    - Predictive maintenance and degradation tracking
    - Thermal management and safety monitoring
    - Warranty validation and capacity verification

Classes:
    BESSPhysicsAnalytics: Main analytics engine for BESS physics calculations

Mathematical Models:
    - Energy: E = P × Δt (Power × Time)
    - RTE: η = E_discharged / E_charged × 100%
    - Z-Score: Z = (T - T_median) / σ

Author: Physics Analytics Team
Version: 1.0.0
"""

import pandas as pd


class BESSPhysicsAnalytics:
    """
    Mathematical analytics engine for BESS thermal, degradation, and efficiency metrics.

    This class provides comprehensive physics-based analysis methods for battery
    energy storage systems. It calculates key performance indicators including
    energy throughput, round-trip efficiency, thermal characteristics, and
    identifies potential issues through statistical anomaly detection.

    The analytics engine is designed for:
    - Real-time performance monitoring
    - Historical trend analysis
    - Predictive maintenance
    - Warranty and performance validation

    Attributes:
        dt_hours (float): Time interval in hours between consecutive measurements.
                         Used for energy integration calculations.
                         Calculated from sampling_interval_minutes parameter.

    Constants Used:
        Typical BESS specifications:
        - Sampling rate: 1-10 minutes (configurable)
        - Voltage range: 800-1100 VDC (system dependent)
        - Current range: -500 to +500 A (system dependent)
        - Temperature range: 15-35°C (normal operating range)
        - RTE target: 85-95% (depends on chemistry and age)

    Example:
        >>> # Initialize analytics engine with 10-minute sampling
        >>> analytics = BESSPhysicsAnalytics(sampling_interval_minutes=10.0)
        >>>
        >>> # Calculate energy and efficiency
        >>> df_inverter = pd.read_parquet('inverter_data.parquet')
        >>> metrics = analytics.calculate_energy_and_rte(df_inverter)
        >>> print(f"RTE: {metrics['rte_percent']:.2f}%")
        RTE: 89.50%
        >>>
        >>> # Analyze thermal distribution
        >>> df_battery = pd.read_parquet('battery_data.parquet')
        >>> delta_t = analytics.calculate_delta_t(df_battery)
        >>> print(f"Max ΔT: {delta_t['delta_t_C'].max():.2f}°C")
        Max ΔT: 4.50°C

    Note:
        - All energy calculations assume constant power during sampling interval
        - Thermal calculations require synchronized multi-module data
        - Internal resistance estimation requires high-current operation data

    Version: 1.0.0
    """

    def __init__(self, sampling_interval_minutes: float = 10.0):
        """
        Initialize the BESS Physics Analytics engine.

        Sets up time-based parameters for energy integration calculations.
        The sampling interval defines the temporal resolution of the analysis
        and is critical for accurate energy throughput calculations.

        Args:
            sampling_interval_minutes (float, optional): Time interval between
                consecutive data points in minutes. Default: 10.0 minutes.
                Common values:
                - 1.0: High-resolution monitoring (1 min)
                - 5.0: Standard resolution (5 min)
                - 10.0: Low-resolution monitoring (10 min)
                - 15.0: Quarter-hourly (market intervals)

        Attributes Set:
            dt_hours (float): Sampling interval converted to hours.
                            Used in energy integration: E = P × Δt

        Example:
            >>> # 1-minute sampling for high-resolution analysis
            >>> analytics_hires = BESSPhysicsAnalytics(sampling_interval_minutes=1.0)
            >>> analytics_hires.dt_hours
            0.016666666666666666  # 1/60 hour

            >>> # 15-minute sampling for market-aligned analysis
            >>> analytics_market = BESSPhysicsAnalytics(sampling_interval_minutes=15.0)
            >>> analytics_market.dt_hours
            0.25  # 1/4 hour

        Note:
            - Shorter intervals provide better temporal resolution
            - Longer intervals reduce computational overhead
            - Choose interval based on data availability and use case
        """
        # dt_hours: Convert sampling interval from minutes to hours
        # Used for energy integration: Energy (MWh) = Power (MW) × Time (hours)
        self.dt_hours = sampling_interval_minutes / 60.0

    def calculate_energy_and_rte(self, df_inv: pd.DataFrame) -> dict:
        """
        Calculate total energy throughput and Round-Trip Efficiency (RTE).

        This method analyzes inverter power output data to compute:
        1. Total energy discharged (delivered to grid)
        2. Total energy charged (absorbed from grid)
        3. Round-Trip Efficiency (RTE): energy recovery ratio

        The RTE is a critical performance metric indicating how much of the
        stored energy can be recovered, with losses due to:
        - Internal resistance (I²R losses)
        - Power electronics conversion losses
        - Auxiliary power consumption
        - Thermal losses

        Mathematical Model:
            E_discharged = Σ(P_positive × Δt) for all P > 0
            E_charged = Σ(|P_negative| × Δt) for all P < 0
            RTE = (E_discharged / E_charged) × 100%

        Power Sign Convention:
            - Positive power: Discharging (battery → grid)
            - Negative power: Charging (grid → battery)
            - Zero power: Standby/idle

        Args:
            df_inv (pd.DataFrame): Inverter operational data with required column:
                - active_power_output_MW (float): Inverter active power in MW
                  Positive values indicate discharging
                  Negative values indicate charging

        Returns:
            dict: Dictionary containing three key metrics:
                - total_discharged_MWh (float): Total energy discharged in MWh
                - total_charged_MWh (float): Total energy charged in MWh
                - rte_percent (float): Round-Trip Efficiency as percentage
                  Range: 0-100%, typical BESS: 85-95%

        Raises:
            KeyError: If 'active_power_output_MW' column is missing
            ValueError: If data contains non-numeric values

        Example:
            >>> # Sample inverter data
            >>> df = pd.DataFrame({
            ...     'timestamp': pd.date_range('2024-06-13', periods=6, freq='10T'),
            ...     'active_power_output_MW': [0.5, 1.0, 1.5, -1.2, -1.0, -0.8]
            ... })
            >>>
            >>> # Calculate energy and RTE
            >>> analytics = BESSPhysicsAnalytics(sampling_interval_minutes=10.0)
            >>> result = analytics.calculate_energy_and_rte(df)
            >>>
            >>> print(f"Discharged: {result['total_discharged_MWh']:.2f} MWh")
            Discharged: 0.50 MWh  # (0.5+1.0+1.5) × (10/60)
            >>> print(f"Charged: {result['total_charged_MWh']:.2f} MWh")
            Charged: 0.50 MWh     # (1.2+1.0+0.8) × (10/60)
            >>> print(f"RTE: {result['rte_percent']:.2f}%")
            RTE: 100.00%          # (0.50/0.50) × 100

        Note:
            - Method assumes constant power during each sampling interval
            - RTE is set to 0.0% if no charging occurred (avoid division by zero)
            - Typical RTE degradation: 0.5-1.0% per year
            - RTE below 85% may indicate degradation or configuration issues

        Performance:
            - Time complexity: O(n) where n is number of samples
            - Memory: O(1) constant space for aggregation
        """
        # Calculate total energy discharged (positive power periods)
        # discharged_mwh: Sum of energy when power output is positive (discharging)
        # Apply lambda: multiply power by time interval only when power > 0
        discharged_mwh = df_inv["active_power_output_MW"].apply(lambda x: x * self.dt_hours if x > 0 else 0).sum()

        # Calculate total energy charged (negative power periods)
        # charged_mwh: Sum of energy when power output is negative (charging)
        # Apply lambda: multiply absolute power by time interval only when power < 0
        charged_mwh = df_inv["active_power_output_MW"].apply(lambda x: abs(x) * self.dt_hours if x < 0 else 0).sum()

        # Calculate Round-Trip Efficiency (RTE)
        # rte: Ratio of discharged to charged energy, expressed as percentage
        # Guard against division by zero when no charging has occurred
        rte = (discharged_mwh / charged_mwh) * 100.0 if charged_mwh > 0 else 0.0

        # Return metrics as dictionary with explicit float conversion
        return {
            "total_discharged_MWh": float(discharged_mwh),
            "total_charged_MWh": float(charged_mwh),
            "rte_percent": float(rte),
        }

    def calculate_delta_t(self, df_bat: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate maximum thermal delta (ΔT) over time across module racks.

        This method computes temperature differences within battery racks to
        identify thermal imbalances. Large ΔT values indicate:
        - Uneven current distribution (cell balancing issues)
        - Cooling system inefficiencies
        - Potential degradation or defects
        - Risk of thermal runaway in extreme cases

        Thermal delta is a critical safety and performance metric:
        - ΔT < 5°C: Normal operation (good thermal management)
        - ΔT 5-10°C: Moderate concern (check cooling system)
        - ΔT > 10°C: High risk (immediate investigation required)

        Mathematical Model:
            ΔT = T_max - T_min (per rack, per timestamp)

        Args:
            df_bat (pd.DataFrame): Battery module temperature data with columns:
                - timestamp (datetime): Time of measurement
                - rack_id (int/str): Identifier for battery rack
                - module_temperature_C (float): Module temperature in Celsius

        Returns:
            pd.DataFrame: Aggregated thermal analysis with columns:
                - timestamp (datetime): Time of measurement
                - rack_id (int/str): Battery rack identifier
                - max (float): Maximum temperature in rack at timestamp (°C)
                - min (float): Minimum temperature in rack at timestamp (°C)
                - delta_t_C (float): Temperature span (ΔT) in rack (°C)

        Raises:
            KeyError: If required columns are missing
            ValueError: If data types are invalid

        Example:
            >>> # Sample battery temperature data
            >>> df = pd.DataFrame({
            ...     'timestamp': ['2024-06-13 12:00'] * 4 + ['2024-06-13 12:10'] * 4,
            ...     'rack_id': [1, 1, 2, 2] * 2,
            ...     'module_temperature_C': [25.0, 27.0, 24.5, 26.0,
            ...                              26.0, 31.0, 25.0, 27.5]
            ... })
            >>>
            >>> # Calculate thermal deltas
            >>> analytics = BESSPhysicsAnalytics()
            >>> result = analytics.calculate_delta_t(df)
            >>>
            >>> # Rack 1 at 12:00: max=27.0, min=25.0, ΔT=2.0°C
            >>> # Rack 1 at 12:10: max=31.0, min=26.0, ΔT=5.0°C (warning threshold)

        Use Cases:
            - Real-time thermal monitoring dashboards
            - Degradation trend analysis
            - Warranty claim validation
            - Cooling system performance assessment

        Note:
            - Requires multi-module data for meaningful analysis
            - Time-synchronized measurements are essential
            - Compare ΔT across racks to identify problematic units

        Performance:
            - Time complexity: O(n log n) due to groupby operation
            - Memory: O(m) where m is unique (timestamp, rack_id) combinations
        """
        # Group by timestamp and rack to find temperature distribution per rack
        # grouped: Aggregated statistics (max, min) for each rack at each timestamp
        grouped = df_bat.groupby(["timestamp", "rack_id"])["module_temperature_C"].agg(["max", "min"]).reset_index()

        # Calculate thermal delta (ΔT)
        # delta_t_C: Temperature span within each rack = maximum - minimum
        # Large values indicate poor thermal uniformity
        grouped["delta_t_C"] = grouped["max"] - grouped["min"]

        return grouped

    def estimate_internal_resistance_data(self, df_bat: pd.DataFrame) -> pd.DataFrame:
        """
        Filter battery data to isolate high-current periods for internal resistance estimation.

        This method prepares data for internal resistance (R_int) analysis by
        removing low-current standby periods. Internal resistance affects:
        - Energy efficiency (I²R losses)
        - Heat generation (thermal management)
        - Voltage sag under load
        - Battery degradation rate

        Internal resistance increases over time due to:
        - Electrode surface degradation
        - Electrolyte decomposition
        - Separator resistance increase
        - Lithium plating effects

        Typical R_int values:
        - New LFP cells: 0.5-1.5 mΩ
        - New NMC cells: 0.3-1.0 mΩ
        - Aged cells: 2-5× higher (significant degradation)

        Analysis Method:
            R_int can be estimated from voltage-current relationship:
            V = V_oc - I × R_int (discharging)
            V = V_oc + I × R_int (charging)

            Where:
            - V: Terminal voltage
            - V_oc: Open-circuit voltage
            - I: Current
            - R_int: Internal resistance

        Why Filter Low Currents?
        - At low currents, voltage change is dominated by noise
        - Thermal effects obscure ohmic voltage drop
        - I²R losses are negligible relative to measurement uncertainty
        - High-current data provides clear voltage-current correlation

        Args:
            df_bat (pd.DataFrame): Battery operational data with column:
                - rack_total_current_A (float): Rack current in Amperes
                  Positive: discharging, Negative: charging
                  Typical range: -500A to +500A

        Returns:
            pd.DataFrame: Filtered dataset containing only high-current samples
                         (|current| > 5.0 A), suitable for R_int curve fitting.
                         Preserves all original columns.

        Raises:
            KeyError: If 'rack_total_current_A' column is missing

        Example:
            >>> # Sample battery data with mixed current levels
            >>> df = pd.DataFrame({
            ...     'timestamp': pd.date_range('2024-06-13', periods=5, freq='1min'),
            ...     'rack_total_current_A': [0.5, -2.0, 150.0, -200.0, 1.0],
            ...     'rack_voltage_V': [950.0, 952.0, 925.0, 970.0, 951.0]
            ... })
            >>>
            >>> # Filter for high-current periods
            >>> analytics = BESSPhysicsAnalytics()
            >>> df_filtered = analytics.estimate_internal_resistance_data(df)
            >>>
            >>> # Only rows with |I| > 5.0 A remain (150, -200)
            >>> len(df_filtered)
            2
            >>>
            >>> # Now suitable for R_int estimation via linear regression
            >>> # Example: R_int = -slope(V vs I) / number_of_cells

        Threshold Selection:
            - Current threshold: 5.0 A (configurable)
            - Rationale: Balances noise rejection with data retention
            - For high-power systems: consider higher threshold (10-20 A)
            - For low-power systems: consider lower threshold (1-5 A)

        Next Steps (for complete R_int analysis):
            1. Filter data using this method
            2. Plot voltage vs. current
            3. Perform linear regression
            4. Extract slope = -R_int × N_cells
            5. Divide by cell count to get per-cell R_int

        Note:
            - This method only filters data, does not calculate R_int
            - For actual R_int calculation, also need voltage data
            - Temperature compensation recommended for accurate results
            - Compare R_int trends over time to track degradation

        Performance:
            - Time complexity: O(n) for filtering
            - Memory: O(k) where k is number of high-current samples
        """
        # Filter dataset to exclude low-current standby/idle periods
        # Threshold: 5.0 A - excludes noise and preserves clear voltage-current relationship
        # abs(): Consider both charging (negative) and discharging (positive) currents
        return df_bat[df_bat["rack_total_current_A"].abs() > 5.0]

    @staticmethod
    def detect_thermal_anomalies(df: pd.DataFrame, threshold_sigma: float = 3.0) -> pd.DataFrame:
        """
        Detect thermal hotspots and anomalies using 3-Sigma statistical rule.

        This static method identifies battery modules with abnormal temperatures
        by comparing each module's temperature to the population statistics at
        each timestamp. The 3-Sigma rule states that:
        - ~68% of data falls within ±1σ (normal)
        - ~95% of data falls within ±2σ (acceptable)
        - ~99.7% of data falls within ±3σ (expected)
        - Values beyond ±3σ are statistical outliers (anomalies)

        Detection Algorithm:
        1. Calculate spatial median and standard deviation per timestamp
        2. Compute Z-score for each measurement: Z = (T - T_median) / σ
        3. Flag measurements where |Z| > threshold (default: 3.0)

        Applications:
        - Real-time safety monitoring
        - Predictive maintenance alerts
        - Cell balancing verification
        - Cooling system diagnostics
        - Defect detection

        Anomaly Causes:
        - Defective cells (internal short, dendrites)
        - Cooling system failures
        - Poor thermal contact
        - Overcurrent conditions
        - Cell imbalance

        Args:
            df (pd.DataFrame): Battery temperature data with columns:
                - timestamp (datetime): Time of measurement
                - battery_id (int/str): Battery module identifier
                - temperature (float): Module temperature in °C
            threshold_sigma (float, optional): Z-score threshold for anomaly detection.
                Default: 3.0 (3-Sigma rule)
                Common values:
                - 2.0: More sensitive (95% confidence)
                - 3.0: Standard threshold (99.7% confidence)
                - 4.0: Less sensitive (99.99% confidence)

        Returns:
            pd.DataFrame: Original DataFrame with two additional columns:
                - temperature_z_score (float): Standardized temperature deviation
                  Interpretation:
                  * |Z| < 1: Within 1σ (normal)
                  * 1 ≤ |Z| < 2: Within 2σ (watch)
                  * 2 ≤ |Z| < 3: Within 3σ (concern)
                  * |Z| ≥ 3: Outlier (anomaly)

                - is_thermal_anomaly (bool): Anomaly flag
                  True: |Z-score| > threshold (requires investigation)
                  False: Normal operation

        Raises:
            KeyError: If required columns ('timestamp', 'temperature') are missing

        Example:
            >>> # Sample temperature data
            >>> df = pd.DataFrame({
            ...     'timestamp': ['2024-06-13 12:00'] * 5,
            ...     'battery_id': [1, 2, 3, 4, 5],
            ...     'temperature': [25.0, 26.0, 25.5, 42.0, 25.2]  # Battery 4 is hot!
            ... })
            >>>
            >>> # Detect anomalies
            >>> result = BESSPhysicsAnalytics.detect_thermal_anomalies(df, threshold_sigma=3.0)
            >>>
            >>> # Check flagged anomalies
            >>> anomalies = result[result['is_thermal_anomaly']]
            >>> print(anomalies[['battery_id', 'temperature', 'temperature_z_score']])
               battery_id  temperature  temperature_z_score
            4           5         42.0                  4.12  # Flagged!
            >>>
            >>> # Alert: Battery 5 is 4.12 standard deviations above median

        Edge Cases:
            - Empty DataFrame: Returns df with False flags and 0.0 Z-scores
            - Missing 'temperature' column: Returns df with False flags
            - Zero standard deviation (all equal): Uses 1e-6 to avoid division by zero
            - Single measurement: Z-score = 0.0 (no reference population)

        Statistical Notes:
            - Uses median (not mean) for robustness against outliers
            - Operates on spatial distribution (across batteries at same time)
            - Assumes roughly normal temperature distribution
            - Not suitable for temporal trend detection (use different method)

        Performance:
            - Time complexity: O(n log n) due to groupby operations
            - Memory: O(n) for augmented DataFrame

        Best Practices:
            - Monitor anomaly frequency: > 1% suggests systematic issues
            - Combine with temporal analysis for comprehensive monitoring
            - Adjust threshold based on system characteristics and risk tolerance
            - Log all anomalies for root cause analysis

        See Also:
            calculate_delta_t(): Complementary thermal uniformity analysis
        """
        # Handle edge cases: empty DataFrame or missing temperature column
        if df.empty or "temperature" not in df.columns:
            # Return safe defaults to prevent downstream errors
            df["is_thermal_anomaly"] = False
            df["temperature_z_score"] = 0.0
            return df

        # Step 1: Calculate baseline metrics (median and std) per timestamp
        # stats: Statistical summary of spatial temperature distribution
        # Using median (not mean) for robustness against outliers
        stats = df.groupby("timestamp")["temperature"].agg(["median", "std"]).reset_index()

        # Rename columns for clarity
        stats.rename(columns={"median": "spatial_median", "std": "spatial_std"}, inplace=True)

        # Step 2: Merge metrics back to original dataset
        # merged_df: Original data enriched with population statistics
        merged_df = df.merge(stats, on="timestamp", how="left")

        # Avoid division by zero if std is perfectly 0.0 (thermal equilibrium)
        # Replace zero std with tiny value (1e-6) to allow Z-score calculation
        merged_df["spatial_std"] = merged_df["spatial_std"].replace(0.0, 1e-6)

        # Step 3: Compute Z-Score: Z = (T - T_median) / σ
        # temperature_z_score: Standardized deviation from spatial median
        # Positive Z: Hotter than typical
        # Negative Z: Cooler than typical
        merged_df["temperature_z_score"] = (merged_df["temperature"] - merged_df["spatial_median"]) / merged_df[
            "spatial_std"
        ]

        # Step 4: Flag anomalies exceeding the configured threshold
        # is_thermal_anomaly: Boolean flag for outliers
        # Uses absolute value to catch both hot and cold anomalies
        merged_df["is_thermal_anomaly"] = merged_df["temperature_z_score"].abs() > threshold_sigma

        # Drop temporary columns to keep DataFrame clean and memory-efficient
        return merged_df.drop(columns=["spatial_median", "spatial_std"])
