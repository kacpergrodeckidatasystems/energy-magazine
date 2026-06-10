import math
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


class ValueUtils:
    """Scalar math utilities for the simulation engine"""

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        return max(min(value, max_val), min_val)


class BESSPhysicsProfile:
    """
    Deterministic physical engine calculating smooth diurnal solar,
    current, and state-of-charge (SoC) profiles.
    """

    def __init__(self, dt: datetime):
        self.time_float = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        self.solar_radiation = self._calculate_solar()
        self.base_current = self._calculate_current()
        self.soc_trend = self._calculate_soc()

    def _calculate_solar(self) -> float:
        if 6.0 <= self.time_float <= 18.0:
            return 900.0 * math.sin((self.time_float - 6.0) / 12.0 * math.pi)
        return 0.0

    def _calculate_current(self) -> float:
        # Negative = Charging (midday sun), Positive = Discharging (evening peak)
        charge_wave = -80.0 * math.exp(-(((self.time_float - 12.5) / 2.5) ** 2))
        discharge_wave = 115.0 * math.exp(-(((self.time_float - 19.5) / 1.8) ** 2))
        return charge_wave + discharge_wave

    def _calculate_soc(self) -> float:
        if self.time_float < 7.0:
            return 40.0
        elif 7.0 <= self.time_float <= 16.0:
            return 40.0 + 45.0 * math.sin((self.time_float - 7.0) / 9.0 * (math.pi / 2))
        elif 16.0 < self.time_float <= 22.0:
            return 30.0 + 55.0 * math.cos((self.time_float - 16.0) / 6.0 * (math.pi / 2))
        return 30.0


class DayGenerator(ABC):
    """Abstract Base Class for whole-day telemetry generators (OCP)"""

    def __init__(self, sampling_interval_minutes: int = 10):
        self.interval = timedelta(minutes=sampling_interval_minutes)

    @abstractmethod
    def generate(self, target_date: datetime) -> pd.DataFrame:
        pass

    def _init_start_time(self, target_date: datetime) -> datetime:
        return datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)


class EnvironmentDayGenerator(DayGenerator):
    """Generates continuous meteorological and environmental data metrics"""

    def generate(self, target_date: datetime) -> pd.DataFrame:
        current_time = self._init_start_time(target_date)
        start_day = current_time.day
        records = []

        while current_time.day == start_day:
            profile = BESSPhysicsProfile(current_time)

            # Ambient temperature delayed peak around 15:30
            base_temp = 24.5 + 2.5 * math.sin((profile.time_float - 9.5) / 12.0 * math.pi)
            solar = profile.solar_radiation

            if solar > 0:
                solar = max(0.0, solar + np.random.normal(0, 10))

            records.append(
                {
                    "timestamp": current_time,
                    "ambient_temp_sensor_01_C": float(base_temp + np.random.normal(0, 0.1)),
                    "ambient_temp_sensor_02_C": float(base_temp + np.random.normal(0, 0.1)),
                    "ambient_temp_sensor_03_C": float(base_temp + np.random.normal(0, 0.1)),
                    "ambient_temp_sensor_04_C_HIGH_ANOMALY": float(base_temp + 8.2 + np.random.normal(0, 0.2)),
                    "ambient_temp_sensor_05_C_LOW_ANOMALY": float(-6.5 + np.random.normal(0, 0.05)),
                    "max_solar_radiation_W_m2": float(solar),
                    "grid_condition_ok": 1 if np.random.rand() > 0.01 else 0,
                }
            )
            current_time += self.interval

        return pd.DataFrame(records)


class InverterDayGenerator(DayGenerator):
    """Generates continuous Power Conversion System (PCS) performance arrays"""

    def generate(self, target_date: datetime) -> pd.DataFrame:
        current_time = self._init_start_time(target_date)
        start_day = current_time.day
        records = []

        while current_time.day == start_day:
            profile = BESSPhysicsProfile(current_time)

            # Scale power output mapping grid values up to +/- 5MW
            active_power = (profile.base_current * 800) / 200000.0
            efficiency = 99.2 - 2.0 * (abs(active_power) / 5.0) ** 2 + np.random.normal(0, 0.05)

            records.append(
                {
                    "timestamp": current_time,
                    "inverter_efficiency_percent": float(ValueUtils.clamp(efficiency, 95.0, 99.5)),
                    "active_power_output_MW": float(active_power + np.random.normal(0, 0.05)),
                    "reactive_power_MVAR": float(np.random.uniform(-0.05, 0.05)),
                }
            )
            current_time += self.interval

        return pd.DataFrame(records)


class BatteryDayGenerator(DayGenerator):
    """Generates multi-rack Battery Management System (BMS) cell telemetry"""

    def generate(self, target_date: datetime) -> pd.DataFrame:
        current_time = self._init_start_time(target_date)
        start_day = current_time.day
        racks = ["rack_01", "rack_02"]
        records = []

        while current_time.day == start_day:
            profile = BESSPhysicsProfile(current_time)

            for rack_id in racks:
                rack_current = float(profile.base_current + np.random.normal(0, 0.5))
                rack_soc = float(profile.soc_trend + np.random.normal(0, 0.1))

                for m_idx in range(1, 6):
                    thermal_gradient = m_idx * 0.7
                    joule_heating = (rack_current**2) * 0.00025

                    # Thermal lag calculation based on I^2R
                    module_temp = 23.5 + thermal_gradient + (joule_heating * 0.06) + np.random.normal(0, 0.05)
                    # Open Circuit Voltage mapped linearly to cell chemistry state
                    module_voltage = 158.0 + (rack_soc - 15.0) * 0.18 + np.random.normal(0, 0.03)
                    module_soc = rack_soc + np.random.normal(0, 0.05)

                    # --- ANOMALY INJECTION MATRIX ---
                    # [Point 1] Voltage Sag / Overvoltage (High internal resistance)
                    if rack_id == "rack_01" and m_idx == 2:
                        module_voltage -= rack_current * 0.08

                    # [Point 2] Local HVAC Failure / Blocked thermal dissipation
                    if rack_id == "rack_02" and m_idx == 4:
                        anomaly_heating = (rack_current**2) * 0.0022
                        module_temp += anomaly_heating + 5.0

                    records.append(
                        {
                            "timestamp": current_time,
                            "rack_id": rack_id,
                            "battery_module_id": f"battery_module_{str(m_idx).zfill(2)}",
                            "module_voltage_V": float(module_voltage),
                            "rack_total_current_A": rack_current,
                            "module_temperature_C": float(module_temp),
                            "soc_percent": float(ValueUtils.clamp(module_soc, 0.0, 100.0)),
                        }
                    )
            current_time += self.interval

        return pd.DataFrame(records)


# --- WRAPPER INTERFACES FOR BACKWARDS COMPATIBILITY WITH ETL PIPELINES ---
def generate_environment_day(target_date: datetime) -> pd.DataFrame:
    return EnvironmentDayGenerator().generate(target_date)


def generate_inverter_day(target_date: datetime) -> pd.DataFrame:
    return InverterDayGenerator().generate(target_date)


def generate_battery_day(target_date: datetime) -> pd.DataFrame:
    return BatteryDayGenerator().generate(target_date)
