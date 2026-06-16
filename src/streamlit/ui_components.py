from datetime import datetime

import pandas as pd

import streamlit as st


def render_sidebar_config(data_loader) -> str:

    st.sidebar.header("📅 Configuration")
    available_dates = data_loader.get_available_dates()

    if not available_dates:
        st.sidebar.warning("No data found in directory! Please trigger the Airflow DAG first.")
        st.stop()

    selected_date_str = st.sidebar.selectbox(
        "Select analysis date:",  # Label for selectbox
        available_dates,  # List of YYYYMMDD strings
        format_func=lambda x: datetime.strptime(x, "%Y%m%d").strftime("%Y-%m-%d"),
    )

    return selected_date_str


def render_hardware_filters(battery_df: pd.DataFrame) -> pd.DataFrame:

    st.sidebar.markdown("---")
    st.sidebar.header("🎛️ Asset Filtering")

    all_racks = sorted(battery_df["rack_id"].unique())

    selected_racks = st.sidebar.multiselect(
        "🗄️ Rack Unit:",  # Label with icon
        options=all_racks,  # All available racks
        default=all_racks,  # Default: select all
    )

    battery_rack_filtered_df = battery_df[battery_df["rack_id"].isin(selected_racks)].copy()

    if not battery_rack_filtered_df.empty:
        battery_rack_filtered_df["global_module_id"] = battery_rack_filtered_df["rack_id"].str.replace(
            "_", " "
        ).str.title() + battery_rack_filtered_df["battery_module_id"].str.replace("battery_module_", "bat")

        available_modules = sorted(battery_rack_filtered_df["global_module_id"].unique())
    else:
        battery_rack_filtered_df["global_module_id"] = []
        available_modules = []

    selected_modules = st.sidebar.multiselect(
        "🔋 Battery Module:",  # Label with icon
        options=available_modules,  # Modules from selected racks
        default=available_modules,  # Default: select all
    )

    return battery_rack_filtered_df[battery_rack_filtered_df["global_module_id"].isin(selected_modules)]


def render_kpi_panel(environment_df: pd.DataFrame, metrics: dict) -> None:

    st.subheader("📊 Key Performance Indicators")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    kpi_col1.metric(
        "Max Ambient Temp",  # Metric label
        f"{environment_df['ambient_temp_sensor_01_C'].max():.1f} °C",  # Formatted value with unit
    )

    kpi_col2.metric(
        "Round-Trip Efficiency (RTE)",  # Metric label
        f"{metrics['rte_percent']:.1f} %",  # Formatted percentage
    )

    kpi_col3.metric(
        "Total Charged (PV)",  # Metric label
        f"{metrics['total_charged_MWh']:.2f} MWh",  # Formatted energy value
    )

    kpi_col4.metric(
        "Total Discharged (Grid)",  # Metric label
        f"{metrics['total_discharged_MWh']:.2f} MWh",  # Formatted energy value
    )

    st.markdown("---")
