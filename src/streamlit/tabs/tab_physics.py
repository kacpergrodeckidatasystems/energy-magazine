"""
Advanced Physical Analytics Tab

Provides in-depth physics-based analysis of BESS performance including:
- State of Energy (SoE) tracking
- Thermal dispersion analysis (Delta-T)
- Internal resistance estimation via voltage-current characteristics
"""

import pandas as pd

import streamlit as st
from src.streamlit.components.analytics_charts import (
    StateOfEnergyChart,
    InternalResistanceScatterChart,
    TemperatureDeltaChart,
)


def render_physics_tab(
    df_inv: pd.DataFrame, df_delta_t: pd.DataFrame, df_resistance_data: pd.DataFrame, dt_hours: float
) -> None:
    """
    Renders Advanced Physical Analytics tab layout.

    Args:
        df_inv: Inverter telemetry dataframe
        df_delta_t: Thermal delta-T analysis dataframe
        df_resistance_data: Internal resistance estimation dataframe
        dt_hours: Sampling interval in hours for energy integration
    """
    st.subheader("🔬 Performance Degradation & Thermal Diagnostics")
    StateOfEnergyChart().render(df_inv, dt_hours)

    st.markdown("---")
    col_an1, col_an2 = st.columns(2)
    with col_an1:
        TemperatureDeltaChart().render(df_delta_t)
    with col_an2:
        InternalResistanceScatterChart().render(df_resistance_data)
