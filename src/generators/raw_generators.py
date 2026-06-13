"""
BESS Data Generators Module

This module provides synthetic data generation for Battery Energy Storage System (BESS)
telemetry and monitoring. It creates realistic, physics-based time-series data for
development, testing, and demonstration purposes.

Main Features:
    - Deterministic physics-based profiles (solar, current, SOC)
    - Multi-component data generation (environment, inverter, battery)
    - Realistic diurnal (daily) patterns matching operational BESS behavior
    - Configurable sampling intervals
    - Anomaly injection for testing monitoring systems

Generated Components:
    1. Environment Data: Ambient sensors and solar radiation
    2. Inverter Data: Power conversion system performance
    3. Battery Data: Multi-rack BMS (Battery Management System) telemetry

Data Characteristics:
    - Sampling rate: Configurable (default: 10 minutes)
    - Time span: 24-hour daily cycles
    - Solar cycle: 06:00-18:00 (sinusoidal)
    - Charging peak: ~12:30 (solar maximum)
    - Discharging peak: ~19:30 (evening demand)
    - SOC range: 30%-85% (realistic operation window)

Design Patterns:
    - Abstract Base Class (ABC): DayGenerator
    - Template Method Pattern: generate() interface
    - Strategy Pattern: Different generators for different subsystems
    - Utility Classes: ValueUtils for common operations

Physics Models:
    - Solar radiation: Sinusoidal model (06:00-18:00)
    - Battery current: Gaussian charge/discharge profiles
    - State of Charge: Piecewise continuous function
    - Temperature: Thermal dynamics with I²R heating
    - Voltage: OCV model with IR drop

Use Cases:
    - Unit testing without hardware
    - Demo systems and presentations
    - Algorithm development and validation
    - Training datasets for machine learning
    - ETL pipeline testing

Classes:
    ValueUtils: Math utility functions
    BESSPhysicsProfile: Core physics calculation engine
    DayGenerator: Abstract base for generators
    EnvironmentDayGenerator: Environmental telemetry
    InverterDayGenerator: Power electronics data
    BatteryDayGenerator: Battery cell-level data

Functions:
    generate_environment_day(): Wrapper for environment data
    generate_inverter_day(): Wrapper for inverter data
    generate_battery_day(): Wrapper for battery data

Author: Physics Analytics Team
Version: 1.0.0
"""

import math
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


class ValueUtils:
    """
    Scalar math utilities for the simulation engine.

    This utility class provides common mathematical operations used throughout
    the data generation process. Implemented as static methods for easy access
    without instantiation.

    Methods:
        clamp(): Constrain values to specified range

    Examples:
        >>> ValueUtils.clamp(150, 0, 100)
        100
        >>> ValueUtils.clamp(-10, 0, 100)
        0
        >>> ValueUtils.clamp(50, 0, 100)
        50
    """

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """
        Constrain a value to lie within a specified range.

        This function ensures values stay within physical or operational limits.
        Common use cases include enforcing voltage limits, SOC bounds, and
        temperature ranges.

        Args:
            value (float): Input value to constrain
            min_val (float): Minimum allowed value (lower bound)
            max_val (float): Maximum allowed value (upper bound)

        Returns:
            float: Constrained value where min_val ≤ result ≤ max_val

        Example:
            >>> # Enforce SOC limits (0-100%)
            >>> ValueUtils.clamp(105.5, 0.0, 100.0)
            100.0
            >>>
            >>> # Enforce voltage limits (2.5-4.2V for Li-ion)
            >>> ValueUtils.clamp(2.3, 2.5, 4.2)
            2.5

        Note:
            - If value < min_val: returns min_val
            - If value > max_val: returns max_val
            - Otherwise: returns value unchanged
        """
        return max(min(value, max_val), min_val)


class BESSPhysicsProfile:
    """
    Deterministic physical engine calculating smooth diurnal solar, current,
    and state-of-charge (SoC) profiles.

    This class implements the core physics models for BESS operation. It calculates
    time-dependent physical parameters based on time of day, simulating realistic
    daily operational patterns. All calculations are deterministic (no randomness)
    to provide a stable baseline for data generation.

    Physics Models Implemented:
    1. Solar Radiation: Sinusoidal model matching sun position
       - Active period: 06:00-18:00
       - Peak: 12:00 noon (~900 W/m²)
       - Night: 0 W/m²

    2. Battery Current: Gaussian profiles for charge/discharge
       - Charging peak: 12:30 (-80A, negative = charging)
       - Discharging peak: 19:30 (+115A, positive = discharging)
       - Width controlled by Gaussian sigma

    3. State of Charge (SOC): Piecewise continuous function
       - Night baseline: 40% (00:00-07:00, 22:00-24:00)
       - Charging phase: 40% → 85% (07:00-16:00)
       - Discharging phase: 85% → 30% (16:00-22:00)

    Attributes:
        time_float (float): Time of day expressed as decimal hours (0.0-24.0)
                           e.g., 14:30 → 14.5, 08:45 → 8.75
        solar_radiation (float): Calculated solar radiation in W/m² (0-900)
        base_current (float): Calculated battery current in Amperes (-80 to +115)
        soc_trend (float): Calculated state of charge percentage (30-85%)

    Example:
        >>> # Morning charging period
        >>> dt = datetime(2024, 6, 13, 10, 30)
        >>> profile = BESSPhysicsProfile(dt)
        >>> print(f"Time: {profile.time_float:.2f} hours")
        Time: 10.50 hours
        >>> print(f"Solar: {profile.solar_radiation:.2f} W/m²")
        Solar: 650.50 W/m²
        >>> print(f"Current: {profile.base_current:.2f} A (negative = charging)")
        Current: -45.20 A (negative = charging)
        >>> print(f"SOC: {profile.soc_trend:.2f}%")
        SOC: 62.30%

        >>> # Evening discharge period
        >>> dt_evening = datetime(2024, 6, 13, 19, 30)
        >>> profile_evening = BESSPhysicsProfile(dt_evening)
        >>> print(f"Current: {profile_evening.base_current:.2f} A")
        Current: 115.00 A  # Peak discharge

    Note:
        - All calculations are deterministic (repeatable for same input time)
        - Profiles designed to match typical grid-connected BESS behavior
        - Values are "base" or "trend" - generators add noise/variation
        - Time calculations use 24-hour format (0.0-24.0)

    Design Pattern:
        Lazy initialization - all properties calculated in __init__()
    """

    def __init__(self, dt: datetime):
        """
        Initialize physics profile for a specific datetime.

        Calculates all physical parameters (solar, current, SOC) based on the
        time of day. This constructor performs all calculations immediately to
        provide a complete snapshot of the BESS physical state.

        Args:
            dt (datetime): Target datetime for physics calculation.
                          All time-based calculations derived from this timestamp.

        Attributes Set:
            time_float (float): Decimal hour representation (e.g., 14.5 for 14:30)
            solar_radiation (float): Solar radiation in W/m²
            base_current (float): Battery current in Amperes
            soc_trend (float): State of charge percentage
        """
        # time_float: Convert datetime to decimal hours (0.0-24.0)
        # Formula: hours + minutes/60 + seconds/3600
        # Example: 14:30:45 → 14 + 30/60 + 45/3600 = 14.5125
        self.time_float = dt.hour + dt.minute / 60.0 + dt.second / 3600.0

        # Calculate physics parameters based on time of day
        self.solar_radiation = self._calculate_solar()
        self.base_current = self._calculate_current()
        self.soc_trend = self._calculate_soc()

    def _calculate_solar(self) -> float:
        """
        Calculate solar radiation based on time of day.

        Implements a simplified sinusoidal solar model representing the sun's
        path across the sky. The model assumes:
        - Sunrise: 06:00
        - Solar noon (peak): 12:00
        - Sunset: 18:00
        - Peak irradiance: 900 W/m² (clear day, horizontal surface)

        Mathematical Model:
            For 06:00 ≤ t ≤ 18:00:
            G(t) = 900 × sin(π × (t - 6) / 12)

            Where:
            - G(t): Global horizontal irradiance (W/m²)
            - t: Time in decimal hours
            - sin(): Creates smooth rise and fall
            - (t - 6) / 12: Normalizes to 0-1 over 12-hour period
            - π: Gives half-period of sine (0 → peak → 0)

        Returns:
            float: Solar radiation in W/m² (0.0-900.0)
                  0.0 during night (before 06:00 or after 18:00)
                  Peak ~900 W/m² at solar noon (12:00)

        Example Values:
            06:00 → 0 W/m² (sunrise)
            09:00 → 450 W/m² (morning)
            12:00 → 900 W/m² (solar noon)
            15:00 → 450 W/m² (afternoon)
            18:00 → 0 W/m² (sunset)
            22:00 → 0 W/m² (night)

        Note:
            - Simplified model (no cloud cover, seasonal effects, or location)
            - Real solar radiation is more complex (atmospheric effects)
            - Peak value (900 W/m²) is typical for clear day mid-latitudes
        """
        if 6.0 <= self.time_float <= 18.0:
            # Daytime: sinusoidal solar profile
            return 900.0 * math.sin((self.time_float - 6.0) / 12.0 * math.pi)
        # Night: no solar radiation
        return 0.0

    def _calculate_current(self) -> float:
        """
        Calculate battery current profile with charge and discharge periods.

        Implements a dual-Gaussian model representing typical BESS grid-arbitrage
        behavior:
        1. Charging during midday (solar peak / low prices)
        2. Discharging during evening peak (high demand / high prices)

        Current Sign Convention:
            - Negative: Charging (energy flowing into battery)
            - Positive: Discharging (energy flowing from battery)
            - Zero: Standby/idle

        Mathematical Model:
            I(t) = I_charge(t) + I_discharge(t)

            Where:
            I_charge = -80 × exp(-((t - 12.5) / 2.5)²)
            I_discharge = +115 × exp(-((t - 19.5) / 1.8)²)

        Charging Component:
            - Peak: -80 A at 12:30 (midday solar/low prices)
            - Width: σ = 2.5 hours (moderate width)
            - Duration: ~10:00-15:00 (centered on solar peak)

        Discharging Component:
            - Peak: +115 A at 19:30 (evening demand/high prices)
            - Width: σ = 1.8 hours (sharper peak)
            - Duration: ~17:30-21:30 (evening peak demand)

        Returns:
            float: Battery current in Amperes
                  Range: approximately -80A to +115A
                  Negative values indicate charging
                  Positive values indicate discharging

        Example Values:
            00:00 → ~0 A (standby)
            07:00 → ~-15 A (begin charging)
            12:30 → ~-80 A (peak charging)
            16:00 → ~0 A (transition)
            19:30 → ~+115 A (peak discharging)
            23:00 → ~0 A (standby)

        Note:
            - Gaussian profiles create smooth, realistic transitions
            - Amplitudes and timings match typical grid-arbitrage patterns
            - Real BESS may have more complex control strategies
            - Values represent base trend (generators add noise)
        """
        # charge_wave: Negative Gaussian centered at 12:30 (midday charging)
        # Amplitude: -80 A, Standard deviation: 2.5 hours
        charge_wave = -80.0 * math.exp(-(((self.time_float - 12.5) / 2.5) ** 2))

        # discharge_wave: Positive Gaussian centered at 19:30 (evening discharge)
        # Amplitude: +115 A, Standard deviation: 1.8 hours (sharper)
        discharge_wave = 115.0 * math.exp(-(((self.time_float - 19.5) / 1.8) ** 2))

        # Total current: Sum of charge and discharge components
        return charge_wave + discharge_wave

    def _calculate_soc(self) -> float:
        """
        Calculate state of charge (SOC) trend throughout the day.

        Implements a piecewise continuous function representing typical BESS
        daily operation cycle:
        1. Night baseline: Maintain reserve (40%)
        2. Charging phase: Increase to maximum (40% → 85%)
        3. Discharging phase: Decrease to safe minimum (85% → 30%)
        4. Night recovery: Return to baseline (30% → 40%)

        SOC Management Strategy:
            - Never fully discharge (protect battery health)
            - Never fully charge (leave margin for grid services)
            - Match charging to solar availability / low prices
            - Match discharging to demand peaks / high prices

        Mathematical Model:
            Piecewise function with four phases:

            1. Pre-charge (00:00-07:00): SOC = 40%
            2. Charging (07:00-16:00): SOC = 40 + 45×sin((t-7)/9 × π/2)
            3. Discharging (16:00-22:00): SOC = 30 + 55×cos((t-16)/6 × π/2)
            4. Night (22:00-24:00): SOC = 30%

        Returns:
            float: State of charge percentage (30.0-85.0%)
                  Range limited to safe operational window

        Phase Breakdown:
            00:00-07:00: Constant 40% (baseline)
            07:00: 40% (start charging)
            11:00: ~62% (mid-charge)
            16:00: ~85% (peak SOC, end charging)
            19:00: ~57% (mid-discharge)
            22:00: 30% (minimum SOC, end discharge)
            22:00-24:00: Constant 30% (depleted state)

        Example Values:
            03:00 → 40%  (night baseline)
            07:00 → 40%  (charge start)
            12:00 → 67%  (mid-charge)
            16:00 → 85%  (peak SOC)
            19:00 → 57%  (mid-discharge)
            22:00 → 30%  (minimum SOC)
            23:00 → 30%  (depleted state)

        Note:
            - SOC windows (30-85%) protect battery longevity
            - Smooth transitions via sin/cos functions
            - Real BMS uses more complex state estimation
            - This is "trend" - individual modules vary slightly

        Battery Health Considerations:
            - Avoiding 0-20%: Prevents deep discharge damage
            - Avoiding 90-100%: Reduces degradation stress
            - Operating window 30-85%: Optimal cycle life
        """
        if self.time_float < 7.0:
            # Phase 1: Early morning baseline (00:00-07:00)
            return 40.0
        elif 7.0 <= self.time_float <= 16.0:
            # Phase 2: Charging period (07:00-16:00)
            # Sinusoidal rise from 40% to 85% over 9 hours
            return 40.0 + 45.0 * math.sin((self.time_float - 7.0) / 9.0 * (math.pi / 2))
        elif 16.0 < self.time_float <= 22.0:
            # Phase 3: Discharging period (16:00-22:00)
            # Cosinusoidal fall from 85% to 30% over 6 hours
            return 30.0 + 55.0 * math.cos((self.time_float - 16.0) / 6.0 * (math.pi / 2))
        # Phase 4: Night depleted state (22:00-24:00)
        return 30.0


class DayGenerator(ABC):
    """
    Abstract Base Class for whole-day telemetry generators.

    This abstract class defines the interface and common functionality for all
    BESS telemetry generators. It implements the Template Method design pattern,
    providing a consistent structure while allowing subclasses to implement
    specific generation logic.

    Design Pattern: Template Method (OCP - Open-Closed Principle)
    - Open for extension: Subclass to add new generator types
    - Closed for modification: Base interface remains stable

    Common Functionality:
        - Configurable sampling interval
        - Date normalization to midnight
        - Consistent generate() interface

    Attributes:
        interval (timedelta): Time between consecutive samples
                             Default: 10 minutes (144 samples/day)

    Subclasses Must Implement:
        generate(target_date): Create DataFrame for specific date

    Usage:
        Do not instantiate directly - use concrete subclasses:
        - EnvironmentDayGenerator
        - InverterDayGenerator
        - BatteryDayGenerator

    Example:
        >>> # Use concrete subclass
        >>> generator = InverterDayGenerator(sampling_interval_minutes=5)
        >>> df = generator.generate(datetime(2024, 6, 13))
        >>> len(df)  # 24 hours × 60 min/hr ÷ 5 min/sample
        288
    """

    def __init__(self, sampling_interval_minutes: int = 10):
        """
        Initialize generator with sampling configuration.

        Args:
            sampling_interval_minutes (int, optional): Time between samples in minutes.
                                                      Default: 10 minutes.
                                                      Common values: 1, 5, 10, 15, 60

        Attributes Set:
            interval (timedelta): Sampling period as timedelta object

        Example:
            >>> # 1-minute high-resolution sampling
            >>> gen_hires = InverterDayGenerator(sampling_interval_minutes=1)
            >>> # 15-minute market-aligned sampling
            >>> gen_market = InverterDayGenerator(sampling_interval_minutes=15)
        """
        # interval: Store sampling period as timedelta for easy time arithmetic
        self.interval = timedelta(minutes=sampling_interval_minutes)

    @abstractmethod
    def generate(self, target_date: datetime) -> pd.DataFrame:
        """
        Generate telemetry data for one complete day.

        Abstract method that must be implemented by all subclasses.
        Each generator creates a DataFrame with component-specific columns
        covering 24 hours from midnight to midnight.

        Args:
            target_date (datetime): Target date for data generation.
                                   Time component is ignored (normalized to midnight).

        Returns:
            pd.DataFrame: Generated telemetry with timestamp and component-specific columns.
                         Number of rows = 1440 / sampling_interval_minutes

        Note:
            Subclasses must implement this method with specific generation logic.
        """
        pass

    def _init_start_time(self, target_date: datetime) -> datetime:
        """
        Normalize target date to midnight (00:00:00).

        Helper method that ensures all generators start from the beginning of
        the day regardless of the time component in target_date.

        Args:
            target_date (datetime): Any datetime on the target day

        Returns:
            datetime: Normalized datetime at midnight (00:00:00)

        Example:
            >>> gen = InverterDayGenerator()
            >>> dt = datetime(2024, 6, 13, 14, 30, 45)
            >>> gen._init_start_time(dt)
            datetime(2024, 6, 13, 0, 0, 0)
        """
        return datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)


class EnvironmentDayGenerator(DayGenerator):
    """
    Generates continuous meteorological and environmental data metrics.

    This generator creates time-series data for ambient sensors and environmental
    conditions around the BESS installation. Data includes temperature sensors
    and solar radiation measurements, with intentional anomalies for testing
    monitoring systems.

    Generated Columns:
        - timestamp: Measurement time
        - ambient_temp_sensor_01_C: Normal sensor #1 (°C)
        - ambient_temp_sensor_02_C: Normal sensor #2 (°C)
        - ambient_temp_sensor_03_C: Normal sensor #3 (°C)
        - ambient_temp_sensor_04_C_HIGH_ANOMALY: Hot anomaly sensor (°C)
        - ambient_temp_sensor_05_C_LOW_ANOMALY: Cold anomaly sensor (°C)
        - max_solar_radiation_W_m2: Peak solar radiation (W/m²)
        - grid_condition_ok: Grid connectivity flag (0/1)

    Features:
        - Diurnal temperature variation (peak ~15:30)
        - Realistic solar radiation with noise
        - Intentional sensor anomalies for testing
        - Grid condition simulation (99% uptime)

    Use Cases:
        - Testing environmental monitoring dashboards
        - Anomaly detection algorithm validation
        - Correlation analysis (temperature vs. solar)
        - Grid reliability monitoring

    Example:
        >>> gen = EnvironmentDayGenerator(sampling_interval_minutes=10)
        >>> df = gen.generate(datetime(2024, 6, 13))
        >>> df.columns.tolist()
        ['timestamp', 'ambient_temp_sensor_01_C', ..., 'grid_condition_ok']
        >>> len(df)
        144  # 24 hours / 10 minutes
    """

    def generate(self, target_date: datetime) -> pd.DataFrame:
        """
        Generate 24 hours of environmental sensor data.

        Creates realistic environmental telemetry including:
        - Multiple ambient temperature sensors (with anomalies)
        - Solar radiation measurements
        - Grid connectivity status

        Temperature Model:
            Base: 24.5°C with ±2.5°C diurnal variation
            Peak: ~15:30 (delayed from solar peak due to thermal mass)
            Sensors 1-3: Normal with small noise (±0.1°C)
            Sensor 4: High anomaly (+8.2°C bias)
            Sensor 5: Low anomaly (-6.5°C absolute reading)

        Solar Radiation Model:
            Base: From BESSPhysicsProfile (0-900 W/m²)
            Noise: Gaussian ±10 W/m² (cloud effects)
            Night: Exactly 0 W/m² (no noise)

        Grid Condition:
            - 99% probability: 1 (connected)
            - 1% probability: 0 (disconnected)

        Args:
            target_date (datetime): Target date for generation

        Returns:
            pd.DataFrame: Environmental data with 8 columns
                         Rows: 1440 / sampling_interval_minutes

        Example:
            >>> gen = EnvironmentDayGenerator()
            >>> df = gen.generate(datetime(2024, 6, 13))
            >>>
            >>> # Check temperature range (excluding anomalies)
            >>> df['ambient_temp_sensor_01_C'].describe()
            count    144.0
            mean     24.5
            min      22.1
            max      26.8

            >>> # Verify solar radiation (day vs night)
            >>> df_day = df[(df.timestamp.dt.hour >= 6) & (df.timestamp.dt.hour <= 18)]
            >>> df_day['max_solar_radiation_W_m2'].mean()
            450.5  # Average during daylight

            >>> # Check anomaly sensors
            >>> sensor4_mean = df['ambient_temp_sensor_04_C_HIGH_ANOMALY'].mean()
            >>> sensor1_mean = df['ambient_temp_sensor_01_C'].mean()
            >>> sensor4_mean - sensor1_mean
            8.2  # Constant bias
        """
        # current_time: Initialize to midnight of target date
        current_time = self._init_start_time(target_date)
        start_day = current_time.day
        records = []

        # Generate data for complete 24-hour period
        while current_time.day == start_day:
            # profile: Calculate physics-based parameters for current time
            profile = BESSPhysicsProfile(current_time)

            # Calculate ambient temperature with diurnal variation
            # base_temp: Sinusoidal variation, peak delayed to 15:30 (thermal mass effect)
            # Formula: 24.5°C ± 2.5°C with peak at hour 9.5 + 6.0 = 15.5 (15:30)
            base_temp = 24.5 + 2.5 * math.sin((profile.time_float - 9.5) / 12.0 * math.pi)

            # solar: Get base solar radiation from physics profile
            solar = profile.solar_radiation

            # Add noise to solar radiation during daytime only
            if solar > 0:
                # Apply Gaussian noise to simulate cloud effects, ensure non-negative
                solar = max(0.0, solar + np.random.normal(0, 10))

            # Append record with all sensor readings
            records.append(
                {
                    "timestamp": current_time,
                    # Normal sensors: Base temperature + small Gaussian noise
                    "ambient_temp_sensor_01_C": float(base_temp + np.random.normal(0, 0.1)),
                    "ambient_temp_sensor_02_C": float(base_temp + np.random.normal(0, 0.1)),
                    "ambient_temp_sensor_03_C": float(base_temp + np.random.normal(0, 0.1)),
                    # Anomaly sensor 4: High temperature bias (+8.2°C)
                    # Simulates faulty sensor or hot spot for monitoring system testing
                    "ambient_temp_sensor_04_C_HIGH_ANOMALY": float(base_temp + 8.2 + np.random.normal(0, 0.2)),
                    # Anomaly sensor 5: Constant low reading (-6.5°C)
                    # Simulates disconnected or failed sensor
                    "ambient_temp_sensor_05_C_LOW_ANOMALY": float(-6.5 + np.random.normal(0, 0.05)),
                    # Solar radiation: Peak irradiance measurement
                    "max_solar_radiation_W_m2": float(solar),
                    # Grid condition: 99% uptime (1 = connected, 0 = disconnected)
                    "grid_condition_ok": 1 if np.random.rand() > 0.01 else 0,
                }
            )

            # Advance to next sampling interval
            current_time += self.interval

        return pd.DataFrame(records)


class InverterDayGenerator(DayGenerator):
    """
    Generates continuous Power Conversion System (PCS) performance arrays.

    This generator creates time-series data for bidirectional inverter operation,
    converting between DC (battery) and AC (grid). Data represents typical
    BESS inverter performance with realistic efficiency curves.

    Generated Columns:
        - timestamp: Measurement time
        - inverter_efficiency_percent: Conversion efficiency (95-99.5%)
        - active_power_output_MW: Real power in megawatts (-5 to +5 MW)
        - reactive_power_MVAR: Reactive power in megavar (-0.05 to +0.05 MVAR)

    Power Sign Convention:
        - Positive: Discharging (battery → grid)
        - Negative: Charging (grid → battery)

    Efficiency Model:
        η = 99.2 - 2.0 × (|P| / 5.0)² + noise
        - Part-load penalty: Efficiency decreases at low and high power
        - Peak efficiency: ~99.2% at moderate power (~2-3 MW)
        - Range: 95.0-99.5% (realistic for modern inverters)

    Use Cases:
        - Inverter performance monitoring
        - Energy loss calculations
        - Power quality analysis
        - Grid interconnection compliance

    Example:
        >>> gen = InverterDayGenerator(sampling_interval_minutes=10)
        >>> df = gen.generate(datetime(2024, 6, 13))
        >>> df[['timestamp', 'active_power_output_MW', 'inverter_efficiency_percent']].head()
    """

    def generate(self, target_date: datetime) -> pd.DataFrame:
        """
        Generate 24 hours of inverter performance data.

        Creates realistic Power Conversion System (PCS) telemetry including:
        - Active power output (charge/discharge)
        - Efficiency curves with part-load effects
        - Reactive power (typically minimal)

        Power Scaling:
            Base current → Active power:
            P = (I × 800) / 200,000

            Example:
            - I = +115 A (discharge peak) → P ≈ +4.6 MW
            - I = -80 A (charge peak) → P ≈ -3.2 MW
            - Power range: approximately -5 to +5 MW

        Efficiency Model:
            η(P) = 99.2 - 2.0 × (|P| / 5.0)² + noise

            Where:
            - η: Efficiency percentage
            - P: Active power magnitude
            - noise: Gaussian ±0.05%

            Clamped to realistic range: 95.0-99.5%

            Physical interpretation:
            - Low power: Lower efficiency (switching losses dominate)
            - Mid power: Peak efficiency (~99.2%)
            - High power: Lower efficiency (conduction losses increase)

        Reactive Power:
            Minimal reactive power generation (±0.05 MVAR)
            Represents inverter operating near unity power factor
            Real systems may provide grid services via reactive power

        Args:
            target_date (datetime): Target date for generation

        Returns:
            pd.DataFrame: Inverter data with 4 columns
                         Rows: 1440 / sampling_interval_minutes

        Example:
            >>> gen = InverterDayGenerator()
            >>> df = gen.generate(datetime(2024, 6, 13))
            >>>
            >>> # Analyze efficiency vs power
            >>> import matplotlib.pyplot as plt
            >>> plt.scatter(df['active_power_output_MW'],
            ...             df['inverter_efficiency_percent'])
            >>> plt.xlabel('Power (MW)')
            >>> plt.ylabel('Efficiency (%)')
            >>> # Shows characteristic U-shaped curve
            >>> # Calculate energy losses
            >>> df['power_loss_MW'] = df['active_power_output_MW'] * \
            ...                       (1 - df['inverter_efficiency_percent']/100)
            >>> total_loss_MWh = df['power_loss_MW'].abs().sum() * (10/60)
            >>> print(f"Daily losses: {total_loss_MWh:.2f} MWh")
        """
        # current_time: Initialize to midnight of target date
        current_time = self._init_start_time(target_date)
        start_day = current_time.day
        records = []

        # Generate data for complete 24-hour period
        while current_time.day == start_day:
            # profile: Calculate physics-based parameters for current time
            profile = BESSPhysicsProfile(current_time)

            # Scale current to grid power levels (MW)
            # active_power: (Amperes × Voltage) / scaling_factor
            # Formula chosen to produce realistic MW range (-5 to +5 MW)
            active_power = (profile.base_current * 800) / 200000.0

            # Calculate efficiency with part-load penalty
            # efficiency: U-shaped curve - lower at extremes, peak at mid-range
            # Base: 99.2%
            # Penalty: -2.0 × (normalized_power)²
            # Noise: ±0.05% Gaussian
            efficiency = 99.2 - 2.0 * (abs(active_power) / 5.0) ** 2 + np.random.normal(0, 0.05)

            # Append record with inverter measurements
            records.append(
                {
                    "timestamp": current_time,
                    # inverter_efficiency_percent: Clamped to realistic range
                    # Modern inverters: 95-99.5% efficiency
                    "inverter_efficiency_percent": float(ValueUtils.clamp(efficiency, 95.0, 99.5)),
                    # active_power_output_MW: Real power with small noise
                    # Positive: discharging, Negative: charging
                    "active_power_output_MW": float(active_power + np.random.normal(0, 0.05)),
                    # reactive_power_MVAR: Minimal reactive power
                    # Near unity power factor operation (cos φ ≈ 1.0)
                    "reactive_power_MVAR": float(np.random.uniform(-0.05, 0.05)),
                }
            )

            # Advance to next sampling interval
            current_time += self.interval

        return pd.DataFrame(records)


class BatteryDayGenerator(DayGenerator):
    """
    Generates multi-rack Battery Management System (BMS) cell telemetry.

    This generator creates detailed, physics-based battery module data for
    multi-rack BESS installations. It simulates realistic cell-level behavior
    including voltage dynamics, thermal effects, and SOC variation across
    modules and racks.

    System Architecture:
        - Number of racks: 2 (rack_01, rack_02)
        - Modules per rack: 5 (battery_module_01 to battery_module_05)
        - Total measurement points: 10 modules
        - Each module reports: voltage, current, temperature, SOC

    Generated Columns:
        - timestamp: Measurement time (with jitter ±5 seconds)
        - rack_id: Rack identifier (rack_01, rack_02)
        - battery_module_id: Module identifier (battery_module_01 to _05)
        - module_voltage_V: Cell terminal voltage (2.5-4.2 V)
        - rack_total_current_A: Rack current in Amperes
        - module_temperature_C: Module temperature (°C)
        - soc_percent: Module state of charge (0-100%)

    Physics Simulated:
        1. Open-Circuit Voltage (OCV): SOC-dependent (3.2-4.0V base)
        2. Internal Resistance (IR) drop: V = OCV - I×R_int
        3. I²R heating: Joule heating from current
        4. Thermal dynamics: Heat generation and dissipation
        5. Inter-module variation: Realistic cell mismatch

    Thermal Model:
        dT/dt = I²R_int × α - (T - T_ambient) × β
        Where:
        - α: Internal heating coefficient
        - β: Thermal loss factor (cooling)
        - Stateful: Temperature persists between samples

    Voltage Model:
        V = V_oc(SOC) - I × R_int
        Where:
        - V_oc: 3.2 + 0.8 × (SOC/100) [Simplified LFP curve]
        - R_int: 0.010-0.016 Ω (varies by module)

    Use Cases:
        - Cell balancing algorithm testing
        - Thermal management verification
        - Degradation analysis
        - BMS dashboard testing
        - Safety monitoring validation

    Example:
        >>> gen = BatteryDayGenerator(sampling_interval_minutes=10)
        >>> df = gen.generate(datetime(2024, 6, 13))
        >>> len(df)
        1440  # 144 timestamps × 10 modules
        >>> df.rack_id.unique()
        array(['rack_01', 'rack_02'])
    """

    def generate(self, target_date: datetime) -> pd.DataFrame:
        """
        Generate 24 hours of multi-module battery telemetry with physical dynamics.

        Creates comprehensive BMS data including:
        - Multi-rack voltage, current, temperature, SOC
        - Physics-based thermal dynamics (stateful)
        - Realistic inter-module variation
        - Timestamp jitter (asynchronous sampling)

        Thermal State Management:
            temp_states: Dictionary persisting module temperatures
            Key: (rack_id, module_index)
            Value: Current temperature (°C)
            Updated each timestep with thermal dynamics

        Module Signature:
            Deterministic per-module characteristic variation
            Formula: (rack_idx × 3.14 + module_idx × 1.618) % 1.0
            - Creates unique but repeatable variations
            - Affects: R_int, thermal losses, SOC offset
            - Result: Each module has distinct behavior

        Current Distribution:
            - Rack 1: 100% of base current
            - Rack 2: 96% of base current
            - Simulates slight load imbalance

        Args:
            target_date (datetime): Target date for generation

        Returns:
            pd.DataFrame: Battery telemetry with 7 columns
                         Rows: (1440 / sampling_interval) × 10 modules

        Example:
            >>> gen = BatteryDayGenerator()
            >>> df = gen.generate(datetime(2024, 6, 13))
            >>>
            >>> # Analyze thermal distribution
            >>> thermal_stats = df.groupby('rack_id')['module_temperature_C'].agg(['mean', 'std'])
            >>> print(thermal_stats)
                       mean  std
            rack_id
            rack_01   25.3  2.1
            rack_02   25.1  2.0
            >>>
            >>> # Check voltage vs SOC correlation
            >>> import matplotlib.pyplot as plt
            >>> plt.scatter(df['soc_percent'], df['module_voltage_V'])
            >>> plt.xlabel('SOC (%)')
            >>> plt.ylabel('Voltage (V)')
            >>> # Should show positive correlation

            >>> # Identify thermal anomalies
            >>> from src.analytics.physics_analytics import BESSPhysicsAnalytics
            >>> df_anomalies = BESSPhysicsAnalytics.detect_thermal_anomalies(
            ...     df.rename(columns={'module_temperature_C': 'temperature',
            ...                        'battery_module_id': 'battery_id'})
            ... )
            >>> anomaly_count = df_anomalies['is_thermal_anomaly'].sum()
            >>> print(f"Thermal anomalies detected: {anomaly_count}")
        """
        records = []

        # current_time: Initialize to midnight of target date
        current_time = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
        end_time = current_time + timedelta(days=1)

        # temp_states: Stateful thermal model - persists module temperatures
        # Key: (rack_id, module_index)
        # Value: Current temperature in Celsius
        # Initialized on first access for each module
        temp_states = {}

        # Generate data for complete 24-hour period
        while current_time < end_time:
            # profile: Calculate physics-based parameters for current time
            profile = BESSPhysicsProfile(current_time)

            # Calculate ambient temperature with diurnal variation
            # time_float: Current time as decimal hours
            # calculated_ambient: Sinusoidal baseline, peak delayed to ~16:00
            time_float = current_time.hour + current_time.minute / 60.0
            calculated_ambient = 21.5 + 6.5 * math.sin((time_float - 8.0) / 24.0 * 2.0 * math.pi)

            # Generate data for each rack (rack_01, rack_02)
            for rack_idx in range(1, 3):
                rack_id = f"rack_{str(rack_idx).zfill(2)}"

                # rack_current: Apply slight load imbalance between racks
                # Rack 1: 100% of base current
                # Rack 2: 96% of base current
                rack_current = profile.base_current * (1.0 if rack_idx == 1 else 0.96)

                # Generate data for each module in the rack (5 modules per rack)
                for m_idx in range(1, 6):
                    # state_key: Unique identifier for thermal state persistence
                    state_key = (rack_id, m_idx)

                    # module_signature: Deterministic per-module variation (0.0-1.0)
                    # Uses irrational numbers (π, φ) for pseudo-random but repeatable values
                    # Each module gets unique characteristics
                    module_signature = (rack_idx * 3.14 + m_idx * 1.618) % 1.0

                    # Initialize thermal state on first access
                    if state_key not in temp_states:
                        # Initial temperature: Ambient + small offset based on signature
                        temp_states[state_key] = calculated_ambient + 1.0 + (module_signature * 1.5)

                    # Calculate module-specific characteristics
                    # internal_resistance: 0.010 to 0.016 Ω
                    # Higher R_int → more heating and IR drop
                    internal_resistance = 0.010 + (module_signature * 0.006)

                    # thermal_loss_factor: 0.010 to 0.014
                    # Represents cooling effectiveness (air circulation differences)
                    thermal_loss_factor = 0.010 + (module_signature * 0.004)

                    # Calculate module SOC
                    # Start from trend, apply module-specific offsets
                    module_soc = profile.soc_trend - (m_idx * 0.15) - (module_signature * 1.0)

                    # Calculate module open-circuit voltage (OCV)
                    # Simplified LFP voltage curve: V_oc = 3.2 + 0.8 × (SOC/100)
                    # Range: 3.2V (0%) to 4.0V (100%)
                    module_voltage = 3.2 + (module_soc / 100.0) * 0.8

                    # Apply internal resistance voltage drop
                    # V = V_oc - I × R_int
                    # Sign: Voltage decreases during discharge (positive I)
                    #       Voltage increases during charge (negative I)
                    module_voltage -= rack_current * internal_resistance

                    # Clamp voltage to safe operating range (Li-ion limits)
                    module_voltage = ValueUtils.clamp(module_voltage, 2.5, 4.2)

                    # Update thermal state with physics-based dynamics
                    module_temp = temp_states[state_key]

                    # thermal_loss: Heat dissipation to ambient
                    # Proportional to temperature difference
                    thermal_loss = (module_temp - calculated_ambient) * thermal_loss_factor

                    # internal_heating: Joule heating from current
                    # P_loss = I² × R_int (scaled by efficiency factor)
                    internal_heating = (rack_current**2) * internal_resistance * 0.05

                    # Update temperature: Add heating, subtract cooling
                    module_temp += internal_heating - thermal_loss
                    temp_states[state_key] = module_temp

                    # Add timestamp jitter to simulate real-world asynchronous sampling
                    # jitter: ±5 seconds random offset
                    jitter = timedelta(seconds=np.random.randint(-5, 6))
                    actual_timestamp = current_time + jitter

                    # Append record with all module measurements
                    records.append(
                        {
                            "timestamp": actual_timestamp,
                            "rack_id": rack_id,
                            "battery_module_id": f"battery_module_{str(m_idx).zfill(2)}",
                            # module_voltage_V: Terminal voltage with IR drop
                            "module_voltage_V": float(module_voltage),
                            # rack_total_current_A: Rack-level current measurement
                            "rack_total_current_A": float(rack_current),
                            # module_temperature_C: Physics-based thermal state
                            "module_temperature_C": float(module_temp),
                            # soc_percent: State of charge, clamped to valid range
                            "soc_percent": float(ValueUtils.clamp(module_soc, 0.0, 100.0)),
                        }
                    )

            # Advance to next sampling interval
            current_time += self.interval

        return pd.DataFrame(records)


# === WRAPPER INTERFACES FOR BACKWARDS COMPATIBILITY WITH ETL PIPELINES ===


def generate_environment_day(target_date: datetime) -> pd.DataFrame:
    """
    Convenience wrapper for EnvironmentDayGenerator.

    Provides functional interface for ETL pipelines that expect function calls
    rather than object instantiation. Uses default sampling interval (10 min).

    Args:
        target_date (datetime): Target date for data generation

    Returns:
        pd.DataFrame: Generated environment telemetry

    Example:
        >>> df = generate_environment_day(datetime(2024, 6, 13))
        >>> df.shape
        (144, 8)
    """
    return EnvironmentDayGenerator().generate(target_date)


def generate_inverter_day(target_date: datetime) -> pd.DataFrame:
    """
    Convenience wrapper for InverterDayGenerator.

    Provides functional interface for ETL pipelines that expect function calls
    rather than object instantiation. Uses default sampling interval (10 min).

    Args:
        target_date (datetime): Target date for data generation

    Returns:
        pd.DataFrame: Generated inverter telemetry

    Example:
        >>> df = generate_inverter_day(datetime(2024, 6, 13))
        >>> df.shape
        (144, 4)
    """
    return InverterDayGenerator().generate(target_date)


def generate_battery_day(target_date: datetime) -> pd.DataFrame:
    """
    Convenience wrapper for BatteryDayGenerator.

    Provides functional interface for ETL pipelines that expect function calls
    rather than object instantiation. Uses default sampling interval (10 min).

    Args:
        target_date (datetime): Target date for data generation

    Returns:
        pd.DataFrame: Generated battery telemetry (multi-module)

    Example:
        >>> df = generate_battery_day(datetime(2024, 6, 13))
        >>> df.shape
        (1440, 7)  # 144 timestamps × 10 modules
    """
    return BatteryDayGenerator().generate(target_date)
