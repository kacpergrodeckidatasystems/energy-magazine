"""
SCADA Live Monitoring Tab

Provides real-time visualization of battery management system (BMS) telemetry,
power conversion system (PCS) performance, and environmental sensors.
"""

import pandas as pd

import streamlit as st
from src.streamlit.components.battery_charts import BatteryTemperatureChart, BatteryVoltageChart
from src.streamlit.components.system_charts import HvacSensorsChart, InverterCorrelationChart


def render_monitoring_tab(df_bat: pd.DataFrame, df_env: pd.DataFrame, df_inv: pd.DataFrame) -> None:
    """
    Renders SCADA Live Monitoring tab layout.

    Displays battery voltage/temperature profiles, inverter power output,
    and HVAC sensor readings in a structured 2-column layout.

    Args:
        df_bat: Battery telemetry dataframe
        df_env: Environment telemetry dataframe
        df_inv: Inverter telemetry dataframe
    """
    st.subheader("🔋 Battery Management System (BMS)")
    col_bat1, col_bat2 = st.columns(2)
    with col_bat1:
        BatteryVoltageChart().render(df_bat)
    with col_bat2:
        BatteryTemperatureChart().render(df_bat)

    st.markdown("---")
    st.subheader("⚡ Power Conversion System (PCS) & Environment")
    col_inv1, col_inv2 = st.columns(2)
    with col_inv1:
        InverterCorrelationChart().render(df_env, df_inv)
    with col_inv2:
        HvacSensorsChart().render(df_env)
