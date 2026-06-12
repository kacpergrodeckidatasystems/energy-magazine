import streamlit as st
import pandas as pd
from datetime import datetime

def render_sidebar_config(data_loader) -> str:
    """Renders date selection in the sidebar and returns the selected date string."""
    st.sidebar.header("📅 Configuration")
    available_dates = data_loader.get_available_dates()

    if not available_dates:
        st.sidebar.warning("No data found in directory! Please trigger the Airflow DAG first.")
        st.stop()

    selected_date_str = st.sidebar.selectbox(
        "Select analysis date:",
        available_dates,
        format_func=lambda x: datetime.strptime(x, "%Y%m%d").strftime("%Y-%m-%d"),
    )
    return selected_date_str

def render_hardware_filters(df_bat: pd.DataFrame) -> pd.DataFrame:
    """Renders hardware multiselect filters and returns the filtered DataFrame."""
    st.sidebar.markdown("---")
    st.sidebar.header("🎛️ Asset Filtering")

    all_racks = sorted(df_bat["rack_id"].unique())
    selected_racks = st.sidebar.multiselect(
        "🗄️ Rack Unit:", 
        options=all_racks, 
        default=all_racks
    )

    df_bat_rack_filtered = df_bat[df_bat["rack_id"].isin(selected_racks)].copy()

    if not df_bat_rack_filtered.empty:
        df_bat_rack_filtered["global_module_id"] = (
            df_bat_rack_filtered["rack_id"].str.replace("_", " ").str.title()
            + " | "
            + df_bat_rack_filtered["battery_module_id"].str.replace("battery_module_", "bat")
        )
        available_modules = sorted(df_bat_rack_filtered["global_module_id"].unique())
    else:
        df_bat_rack_filtered["global_module_id"] = []
        available_modules = []

    selected_modules = st.sidebar.multiselect(
        "🔋 Battery Module:",
        options=available_modules,
        default=available_modules
    )

    return df_bat_rack_filtered[df_bat_rack_filtered["global_module_id"].isin(selected_modules)]

def render_kpi_panel(df_env: pd.DataFrame, metrics: dict) -> None:
    """Renders the top KPI metrics container."""
    st.subheader("📊 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Max Ambient Temp", f"{df_env['ambient_temp_sensor_01_C'].max():.1f} °C")
    col2.metric("Round-Trip Efficiency (RTE)", f"{metrics['rte_percent']:.1f} %")
    col3.metric("Total Charged (PV)", f"{metrics['total_charged_MWh']:.2f} MWh")
    col4.metric("Total Discharged (Grid)", f"{metrics['total_discharged_MWh']:.2f} MWh")
    st.markdown("---")