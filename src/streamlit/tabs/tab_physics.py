import streamlit as st
import pandas as pd
from src.streamlit.components.analytics_charts import EnergyStateOfEnergyChart, InternalResistanceScatterChart, ThermalDeltaTChart

def render_physics_tab(df_inv: pd.DataFrame, df_delta_t: pd.DataFrame, df_res_data: pd.DataFrame, dt_hours: float) -> None:
    """Renders Advanced Physical Analytics tab layout."""
    st.subheader("🔬 Performance Degradation & Thermal Diagnostics")
    EnergyStateOfEnergyChart().render(df_inv, dt_hours)

    st.markdown("---")
    col_an1, col_an2 = st.columns(2)
    with col_an1:
        ThermalDeltaTChart().render(df_delta_t)
    with col_an2:
        InternalResistanceScatterChart().render(df_res_data)