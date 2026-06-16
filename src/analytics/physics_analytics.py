"""
Physics Analytics Module.
BESS physics-based analytics: RTE, thermal delta, internal resistance, anomaly detection.
Models: E=P×Δt, RTE=E_out/E_in×100%, Z=(T-T_median)/σ.
"""

import pandas as pd


class BESSPhysicsAnalytics:
    """
    BESS analytics engine for energy, RTE, thermal analysis, and anomaly detection.
    Sampling interval configurable (default 10 min). Target RTE: 85-95%.
    """

    def __init__(self, sampling_interval_minutes: float = 10.0):
        """Initialize analytics engine with sampling interval."""
        self.sampling_interval_hours = sampling_interval_minutes / 60.0

    def calculate_energy_and_rte(self, inverter_df: pd.DataFrame) -> dict:
        """
        Calculate energy throughput and RTE.
        RTE = (E_discharged / E_charged) × 100%. Returns dict with MWh values and RTE%.
        """
        discharged_mwh = (
            inverter_df["active_power_output_MW"]
            .apply(lambda x: x * self.sampling_interval_hours if x > 0 else 0)
            .sum()
        )
        charged_mwh = (
            inverter_df["active_power_output_MW"]
            .apply(lambda x: abs(x) * self.sampling_interval_hours if x < 0 else 0)
            .sum()
        )
        rte = (discharged_mwh / charged_mwh) * 100.0 if charged_mwh > 0 else 0.0
        return {
            "total_discharged_MWh": float(discharged_mwh),
            "total_charged_MWh": float(charged_mwh),
            "rte_percent": float(rte),
        }

    def calculate_temperature_delta(self, battery_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate thermal delta (ΔT=T_max-T_min) per rack per timestamp.
        ΔT<5°C: normal, 5-10°C: concern, >10°C: high risk. Returns DataFrame with delta_t_C column.
        """
        grouped = battery_df.groupby(["timestamp", "rack_id"])["module_temperature_C"].agg(["max", "min"]).reset_index()
        grouped["delta_t_C"] = grouped["max"] - grouped["min"]
        return grouped

    def estimate_internal_resistance_data(self, battery_df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter data for internal resistance estimation (|current| > 5A).
        Returns filtered DataFrame suitable for R_int curve fitting.
        """
        return battery_df[battery_df["rack_total_current_A"].abs() > 5.0]

    @staticmethod
    def detect_thermal_anomalies(temperature_df: pd.DataFrame, threshold_sigma: float = 3.0) -> pd.DataFrame:
        """
        Detect thermal anomalies using 3-Sigma rule (Z-score analysis).
        Z=(T-T_median)/σ. Flags |Z|>threshold. Returns DataFrame with z_score and is_thermal_anomaly columns.
        """
        if temperature_df.empty or "temperature" not in temperature_df.columns:
            temperature_df["is_thermal_anomaly"] = False
            temperature_df["temperature_z_score"] = 0.0
            return temperature_df

        stats = temperature_df.groupby("timestamp")["temperature"].agg(["median", "std"]).reset_index()
        stats.rename(columns={"median": "spatial_median", "std": "spatial_std"}, inplace=True)
        merged_df = temperature_df.merge(stats, on="timestamp", how="left")
        merged_df["spatial_std"] = merged_df["spatial_std"].replace(0.0, 1e-6)
        merged_df["temperature_z_score"] = (merged_df["temperature"] - merged_df["spatial_median"]) / merged_df[
            "spatial_std"
        ]
        merged_df["is_thermal_anomaly"] = merged_df["temperature_z_score"].abs() > threshold_sigma
        return merged_df.drop(columns=["spatial_median", "spatial_std"])
