import numpy as np
import pandas as pd
import pytest

from src.analytics.physics_analytics import BESSPhysicsAnalytics


def test_calculate_energy_and_rte_normal_operation():
    """Validates Round-Trip Efficiency calculation under controlled charging/discharging."""
    analytics = BESSPhysicsAnalytics(sampling_interval_minutes=60.0)  # 1 hour dt

    df_inv = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2026-06-10 12:00:00"), pd.Timestamp("2026-06-10 13:00:00")],
            "active_power_output_MW": [-2.0, 1.8],  # Charged 2 MWh, Discharged 1.8 MWh
        }
    )

    metrics = analytics.calculate_energy_and_rte(df_inv)

    assert metrics["total_charged_MWh"] == 2.0
    assert metrics["total_discharged_MWh"] == 1.8
    assert metrics["rte_percent"] == pytest.approx(90.0)


def test_calculate_delta_t():
    """Validates that temperature dispersion maximum delta is extracted correctly."""
    analytics = BESSPhysicsAnalytics()
    df_bat = pd.DataFrame(
        {
            "timestamp": [pd.Timestamp("2026-06-10 12:00:00")] * 3,
            "rack_id": ["rack_01", "rack_01", "rack_01"],
            "module_temperature_C": [25.0, 28.5, 24.0],
        }
    )

    df_delta = analytics.calculate_delta_t(df_bat)

    assert df_delta.loc[0, "delta_t_C"] == pytest.approx(4.5)  #

def test_detect_thermal_anomalies_nominal_and_outlier():
    """Verifies that 3-Sigma rule correctly flags an explicit temperature hotspot outlier."""
    timestamps = pd.date_range(start="2026-06-10 00:00:00", periods=5, freq="MIN")
    data = []

    # Generate balanced baseline data (~25 degC) for 21 stable batteries
    for t in timestamps:
        for i in range(1, 21):
            data.append({"timestamp": t, "battery_id": f"bat_{i}", "temperature": 25.0 + np.random.normal(0, 0.1)})

    # Inject a severe thermal anomaly (hotspot) on battery 99
    for t in timestamps:
        data.append({"timestamp": t, "battery_id": "bat_99", "temperature": 42.0}) # Extreme deviation

    df = pd.DataFrame(data)
    analytics_engine = BESSPhysicsAnalytics()

    # Execute statistical detection
    result_df = analytics_engine.detect_thermal_anomalies(df, threshold_sigma=3.0)

    # Assertions
    assert "is_thermal_anomaly" in result_df.columns
    assert "temperature_z_score" in result_df.columns

    # Filter anomalies
    anomalies = result_df[result_df["is_thermal_anomaly"] == True]
    normal_cells = result_df[result_df["is_thermal_anomaly"] == False]

    # Verify bat_5 was isolated as the anomaly across all timesteps
    assert not anomalies.empty
    assert (anomalies["battery_id"] == "bat_99").all()
    assert (normal_cells["battery_id"] != "bat_99").all()
