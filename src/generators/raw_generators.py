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
        """Generates dynamic multi-rack battery submodule physics time-series"""
        records = []
        current_time = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
        end_time = current_time + timedelta(days=1)

        temp_states = {}

        while current_time < end_time:
            profile = BESSPhysicsProfile(current_time)
            
            time_float = current_time.hour + current_time.minute / 60.0
            calculated_ambient = 21.5 + 6.5 * math.sin((time_float - 8.0) / 24.0 * 2.0 * math.pi)

            for rack_idx in range(1, 3):
                rack_id = f"rack_{str(rack_idx).zfill(2)}"
                
                rack_current = profile.base_current * (1.0 if rack_idx == 1 else 0.96)

                for m_idx in range(1, 6):
                    state_key = (rack_id, m_idx)
                    
                    module_signature = (rack_idx * 3.14 + m_idx * 1.618) % 1.0
                    
                    if state_key not in temp_states:
                        temp_states[state_key] = calculated_ambient + 1.0 + (module_signature * 1.5)

                    internal_resistance = 0.010 + (module_signature * 0.006) # od 0.010 do 0.016 Ohm
                    thermal_loss_factor = 0.010 + (module_signature * 0.004) # delikatne różnice w cyrkulacji powietrza

                    module_soc = profile.soc_trend - (m_idx * 0.15) - (module_signature * 1.0)
                    module_voltage = 3.2 + (module_soc / 100.0) * 0.8
                    
                    module_voltage -= rack_current * internal_resistance

                    module_voltage = ValueUtils.clamp(module_voltage, 2.5, 4.2)

                    module_temp = temp_states[state_key]
                    thermal_loss = (module_temp - calculated_ambient) * thermal_loss_factor
                    internal_heating = (rack_current ** 2) * internal_resistance * 0.05
                    
                    module_temp += internal_heating - thermal_loss
                    temp_states[state_key] = module_temp

                    jitter = timedelta(seconds=np.random.randint(-5, 6))
                    actual_timestamp = current_time + jitter

                    records.append(
                        {
                            "timestamp": actual_timestamp,
                            "rack_id": rack_id,
                            "battery_module_id": f"battery_module_{str(m_idx).zfill(2)}",
                            "module_voltage_V": float(module_voltage),
                            "rack_total_current_A": float(rack_current),
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
