import pandas as pd


class BESSPhysicsAnalytics:
    """Mathematical analytics engine for BESS thermal, degradation, and efficiency metrics"""

    def __init__(self, sampling_interval_minutes: float = 10.0):
        self.dt_hours = sampling_interval_minutes / 60.0

    def calculate_energy_and_rte(self, df_inv: pd.DataFrame) -> dict:
        """Calculates total aggregated energy throughput and Round-Trip Efficiency (RTE)"""
        # Separate power metrics into directional arrays (Positive = Discharge, Negative = Charge)
        discharged_mwh = df_inv["active_power_output_MW"].apply(lambda x: x * self.dt_hours if x > 0 else 0).sum()
        charged_mwh = df_inv["active_power_output_MW"].apply(lambda x: abs(x) * self.dt_hours if x < 0 else 0).sum()

        rte = (discharged_mwh / charged_mwh) * 100.0 if charged_mwh > 0 else 0.0

        return {
            "total_discharged_MWh": float(discharged_mwh),
            "total_charged_MWh": float(charged_mwh),
            "rte_percent": float(rte),
        }

    def calculate_delta_t(self, df_bat: pd.DataFrame) -> pd.DataFrame:
        """Calculates the maximum thermal delta (Delta-T) over time across module racks"""
        # Group by timestamp and rack to find cell temperature distribution dispersion
        grouped = df_bat.groupby(["timestamp", "rack_id"])["module_temperature_C"].agg(["max", "min"]).reset_index()
        grouped["delta_t_C"] = grouped["max"] - grouped["min"]
        return grouped

    def estimate_internal_resistance_data(self, df_bat: pd.DataFrame) -> pd.DataFrame:
        """Filters out standby periods to isolate high-current points for R_int curve slope estimation"""
        # Exclude low-current noise to preserve clear voltage-vs-current cross-correlations
        return df_bat[df_bat["rack_total_current_A"].abs() > 5.0]
