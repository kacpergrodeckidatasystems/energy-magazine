"""
BESS synthetic data generators for telemetry and monitoring.
Physics-based profiles for environment, inverter, and battery subsystems.
"""

import math
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


class BESSMathConstraints:
    """Math utility functions for BESS simulation engine."""

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """Constrain value to specified range [min_val, max_val]."""
        return max(min(value, max_val), min_val)


class BESSPhysicsProfile:
    """
    Deterministic physics engine for BESS profiles (solar, current, SOC).
    Calculates time-dependent physical parameters for realistic daily patterns.
    """

    def __init__(self, target_datetime: datetime):
        """Initialize physics profile for a specific datetime."""
        # time_decimal_hours: Time as decimal hours (0.0-24.0)
        self.time_decimal_hours = target_datetime.hour + target_datetime.minute / 60.0 + target_datetime.second / 3600.0

        # solar_radiation: Calculated solar radiation in W/m²
        self.solar_radiation = self._calculate_solar()
        # base_current: Battery current in Amperes (-80 to +115)
        self.base_current = self._calculate_current()
        # soc_trend: State of charge percentage (30-85%)
        self.soc_trend = self._calculate_soc()

    def _calculate_solar(self) -> float:
        """Calculate solar radiation using sinusoidal model (06:00-18:00, peak 900W/m² at 12:00)."""
        if 6.0 <= self.time_decimal_hours <= 18.0:
            return 900.0 * math.sin((self.time_decimal_hours - 6.0) / 12.0 * math.pi)
        return 0.0

    def _calculate_current(self) -> float:
        """
        Calculate battery current with dual-Gaussian model (charging peak -80A at 12:30, discharging peak +115A at 19:30).
        Negative=charging, Positive=discharging.
        """
        # charge_wave: Midday charging, -80A peak at 12:30
        charge_wave = -80.0 * math.exp(-(((self.time_decimal_hours - 12.5) / 2.5) ** 2))
        # discharge_wave: Evening discharge, +115A peak at 19:30
        discharge_wave = 115.0 * math.exp(-(((self.time_decimal_hours - 19.5) / 1.8) ** 2))
        return charge_wave + discharge_wave

    def _calculate_soc(self) -> float:
        """
        Calculate SOC trend using piecewise function (40% baseline, 40→85% charging 07-16h, 85→30% discharging 16-22h).
        Range: 30-85% for battery health.
        """
        if self.time_decimal_hours < 7.0:
            return 40.0
        elif 7.0 <= self.time_decimal_hours <= 16.0:
            return 40.0 + 45.0 * math.sin((self.time_decimal_hours - 7.0) / 9.0 * (math.pi / 2))
        elif 16.0 < self.time_decimal_hours <= 22.0:
            return 30.0 + 55.0 * math.cos((self.time_decimal_hours - 16.0) / 6.0 * (math.pi / 2))
        return 30.0


class BESSDayGenerator(ABC):
    """Abstract base class for generating 24-hour BESS synthetic telemetry data with configurable sampling intervals."""

    def __init__(self, sampling_interval_minutes: int = 10):
        """
        Initialize generator with sampling configuration.
        Args:
            sampling_interval_minutes (int): Time interval between samples in minutes (default: 10).
        """

        self.interval = timedelta(minutes=sampling_interval_minutes)

    @abstractmethod
    def generate(self, target_date: datetime) -> pd.DataFrame:
        """Abstract method to generate a day's worth of data for the target date."""
        pass

    def _normalize_to_midnight(self, target_date: datetime) -> datetime:
        """
        Normalize target date to midnight (00:00:00).
        """
        return datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)


class EnvironmentDayGenerator(BESSDayGenerator):
    """
    Generates environmental telemetry (5 temp sensors with anomalies, solar radiation, grid status).
    Includes intentional anomalies (sensor 4: +8.2°C bias, sensor 5: -6.5°C constant).
    """

    def generate(self, target_date: datetime) -> pd.DataFrame:
        """Generate 24h environmental sensor data with diurnal patterns and anomalies."""
        # current_time: Midnight of target date
        current_time = self._normalize_to_midnight(target_date)
        start_day = current_time.day
        records = []

        while current_time.day == start_day:
            # physics_profile: Physics parameters for current time
            physics_profile = BESSPhysicsProfile(current_time)
            # base_temp: 24.5°C ± 2.5°C diurnal variation, peak at 15:30
            base_temp = 24.5 + 2.5 * math.sin((physics_profile.time_decimal_hours - 9.5) / 12.0 * math.pi)
            # solar: Base solar radiation with noise
            solar = physics_profile.solar_radiation
            if solar > 0:
                solar = max(0.0, solar + np.random.normal(0, 10))
            records.append(
                {
                    "timestamp": current_time,
                    "ambient_temp_sensor_01_C": float(base_temp + np.random.normal(0, 0.1)),
                    "ambient_temp_sensor_02_C": float(base_temp + np.random.normal(0, 0.1)),
                    "ambient_temp_sensor_03_C": float(base_temp + np.random.normal(0, 0.1)),
                    "ambient_temp_sensor_04_C_HIGH_ANOMALY": float(
                        base_temp + 8.2 + np.random.normal(0, 0.2)
                    ),  # High anomaly
                    "ambient_temp_sensor_05_C_LOW_ANOMALY": float(-6.5 + np.random.normal(0, 0.05)),  # Low anomaly
                    "max_solar_radiation_W_m2": float(solar),
                    "grid_condition_ok": 1 if np.random.rand() > 0.01 else 0,  # 99% uptime
                }
            )
            current_time += self.interval

        return pd.DataFrame(records)


class InverterDayGenerator(BESSDayGenerator):
    """
    Generates PCS performance data (efficiency 95-99.5%, active power ±5MW, reactive power).
    Efficiency model: η=99.2-2.0×(|P|/5.0)². Positive power=discharging, Negative=charging.
    """

    def generate(self, target_date: datetime) -> pd.DataFrame:
        """Generate 24h inverter performance data with U-shaped efficiency curve."""
        # current_time: Midnight of target date
        current_time = self._normalize_to_midnight(target_date)
        start_day = current_time.day
        records = []

        while current_time.day == start_day:
            physics_profile = BESSPhysicsProfile(current_time)
            # active_power: Scale to MW range (-5 to +5)
            active_power = (physics_profile.base_current * 800) / 200000.0
            # efficiency: U-shaped curve with part-load penalty
            efficiency = 99.2 - 2.0 * (abs(active_power) / 5.0) ** 2 + np.random.normal(0, 0.05)
            records.append(
                {
                    "timestamp": current_time,
                    "inverter_efficiency_percent": float(
                        BESSMathConstraints.clamp(efficiency, 95.0, 99.5)
                    ),  # Clamped 95-99.5%
                    "active_power_output_MW": float(active_power + np.random.normal(0, 0.05)),  # Real power
                    "reactive_power_MVAR": float(np.random.uniform(-0.05, 0.05)),  # Minimal reactive power
                }
            )
            current_time += self.interval

        return pd.DataFrame(records)


class BatteryDayGenerator(BESSDayGenerator):
    """
    Generates multi-rack BMS telemetry (2 racks × 5 modules, voltage, current, temp, SOC).
    Physics: OCV model V=3.2+0.8×(SOC/100), IR drop, I²R heating, thermal dynamics (stateful).
    """

    def generate(self, target_date: datetime) -> pd.DataFrame:
        """Generate 24h battery telemetry with stateful thermal model and per-module variation."""
        records = []
        # current_time: Midnight of target date
        current_time = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
        end_time = current_time + timedelta(days=1)
        # thermal_state_cache: Stateful thermal model, key=(rack_id, module_index), value=temp_C
        thermal_state_cache = {}

        while current_time < end_time:
            physics_profile = BESSPhysicsProfile(current_time)
            # ambient_temperature: Ambient temperature with diurnal variation
            time_decimal_hours = current_time.hour + current_time.minute / 60.0
            ambient_temperature = 21.5 + 6.5 * math.sin((time_decimal_hours - 8.0) / 24.0 * 2.0 * math.pi)

            for rack_idx in range(1, 3):
                rack_id = f"rack_{str(rack_idx).zfill(2)}"
                # rack_current: Rack 1=100%, Rack 2=96% of base current
                rack_current = physics_profile.base_current * (1.0 if rack_idx == 1 else 0.96)

                for module_index in range(1, 6):
                    # thermal_state_key: Thermal state identifier
                    thermal_state_key = (rack_id, module_index)
                    # module_variation_factor: Deterministic per-module variation 0-1
                    module_variation_factor = (rack_idx * 3.14 + module_index * 1.618) % 1.0

                    if thermal_state_key not in thermal_state_cache:
                        thermal_state_cache[thermal_state_key] = (
                            ambient_temperature + 1.0 + (module_variation_factor * 1.5)
                        )

                    # internal_resistance: 0.010-0.016 Ω
                    internal_resistance = 0.010 + (module_variation_factor * 0.006)
                    # thermal_loss_factor: 0.010-0.014 cooling effectiveness
                    thermal_loss_factor = 0.010 + (module_variation_factor * 0.004)
                    # module_soc: SOC with per-module offset
                    module_soc = physics_profile.soc_trend - (module_index * 0.15) - (module_variation_factor * 1.0)
                    # module_voltage: OCV - IR drop, V=3.2+0.8×(SOC/100)-I×R
                    module_voltage = 3.2 + (module_soc / 100.0) * 0.8
                    module_voltage -= rack_current * internal_resistance
                    module_voltage = BESSMathConstraints.clamp(module_voltage, 2.5, 4.2)

                    # module_temp: Update thermal state with I²R heating and cooling
                    module_temp = thermal_state_cache[thermal_state_key]
                    thermal_loss = (module_temp - ambient_temperature) * thermal_loss_factor
                    internal_heating = (rack_current**2) * internal_resistance * 0.05
                    module_temp += internal_heating - thermal_loss
                    thermal_state_cache[thermal_state_key] = module_temp

                    # jitter: ±5s timestamp offset
                    jitter = timedelta(seconds=np.random.randint(-5, 6))
                    actual_timestamp = current_time + jitter

                    records.append(
                        {
                            "timestamp": actual_timestamp,
                            "rack_id": rack_id,
                            "battery_module_id": f"battery_module_{str(module_index).zfill(2)}",
                            "module_voltage_V": float(module_voltage),
                            "rack_total_current_A": float(rack_current),
                            "module_temperature_C": float(module_temp),
                            "soc_percent": float(BESSMathConstraints.clamp(module_soc, 0.0, 100.0)),
                        }
                    )

            current_time += self.interval

        return pd.DataFrame(records)


def generate_environment_day(target_date: datetime) -> pd.DataFrame:
    """Wrapper for EnvironmentDayGenerator with default 10-min sampling."""
    return EnvironmentDayGenerator().generate(target_date)


def generate_inverter_day(target_date: datetime) -> pd.DataFrame:
    """Wrapper for InverterDayGenerator with default 10-min sampling."""
    return InverterDayGenerator().generate(target_date)


def generate_battery_day(target_date: datetime) -> pd.DataFrame:
    """Wrapper for BatteryDayGenerator with default 10-min sampling."""
    return BatteryDayGenerator().generate(target_date)
