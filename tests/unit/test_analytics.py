import pandas as pd
import pytest

from src.streamlit.physics_analytics import BESSPhysicsAnalytics


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
