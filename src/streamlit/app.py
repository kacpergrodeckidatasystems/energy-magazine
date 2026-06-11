import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from src.streamlit.components.analytics_charts import (
    EnergyStateOfEnergyChart,
    InternalResistanceScatterChart,
    ThermalDeltaTChart,
)
from src.streamlit.components.battery_charts import BatteryTemperatureChart, BatteryVoltageChart
from src.streamlit.components.system_charts import HvacSensorsChart, InverterCorrelationChart
from src.streamlit.data_loader import BESSDataLoader
from src.streamlit.physics_analytics import BESSPhysicsAnalytics

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="BESS Telemetry Dashboard", page_icon="🔋", layout="wide")
st.title("🔋 BESS Real-Time Diagnostic Dashboard")

data_dir = os.getenv("DATA_DIR", "./data/bronze")
data_loader = BESSDataLoader(base_dir=data_dir)


@st.cache_data(ttl=0)
def get_dates(loader):
    return loader.get_available_dates()


# Initialize core engines
physics_engine = BESSPhysicsAnalytics(sampling_interval_minutes=10.0)

# Instantiate chart components
chart_voltage = BatteryVoltageChart()
chart_temperature = BatteryTemperatureChart()
chart_inverter = InverterCorrelationChart()
chart_hvac = HvacSensorsChart()

chart_soe = EnergyStateOfEnergyChart()
chart_delta_t = ThermalDeltaTChart()
chart_resistance = InternalResistanceScatterChart()

# --- SIDEBAR: DATE SELECTION ---
st.sidebar.header("📅 Configuration")
available_dates = data_loader.get_available_dates()

if available_dates:
    selected_date_str = st.sidebar.selectbox(
        "Select analysis date:",
        available_dates,
        format_func=lambda x: datetime.strptime(x, "%Y%m%d").strftime("%Y-%m-%d"),
    )
else:
    st.sidebar.warning("No data found in bronze directory! Please trigger the Airflow DAG first.")
    st.stop()


@st.cache_data
def cached_load(date_str: str):
    return data_loader.load_daily_data(date_str)


# Load data from bronze tier
df_env, df_inv, df_bat = cached_load(selected_date_str)

if df_env is not None and df_inv is not None and df_bat is not None:
    # ==========================================
    # --- SIDEBAR: CASCADING HARDWARE FILTERS ---
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.header("🎛️ Asset Filtering")

    all_racks = sorted(df_bat["rack_id"].unique())
    selected_racks = st.sidebar.multiselect(
        "🗄️ Rack Unit:", 
        options=all_racks, 
        default=all_racks,
        help="Odznaczenie jednostki rack automatycznie ukryje przypisane do niej moduły."
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
        default=available_modules,
        help="Wybierz unikalne moduły z listy od 0 do 10, aby izolować ich charakterystyki robocze."
    )

    df_bat_filtered = df_bat_rack_filtered[df_bat_rack_filtered["global_module_id"].isin(selected_modules)]

    if df_bat_filtered.empty:
        st.warning("⚠️ Odznaczono wszystkie zasoby sprzętowe. Wybierz przynajmniej jeden moduł bateryjny w panelu bocznym, aby wyświetlić telemetrię SCADA.")
        st.stop()

    # Execute physical analytics calculations
    metrics = physics_engine.calculate_energy_and_rte(df_inv)
    df_delta_t = physics_engine.calculate_delta_t(df_bat_filtered)
    df_res_data = physics_engine.estimate_internal_resistance_data(df_bat_filtered)

    # --- TOP KPI METRICS PANEL ---
    st.subheader("📊 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Max Ambient Temp", f"{df_env['ambient_temp_sensor_01_C'].max():.1f} °C")
    col2.metric("Round-Trip Efficiency (RTE)", f"{metrics['rte_percent']:.1f} %")
    col3.metric("Total Charged (PV)", f"{metrics['total_charged_MWh']:.2f} MWh")
    col4.metric("Total Discharged (Grid)", f"{metrics['total_discharged_MWh']:.2f} MWh")

    st.markdown("---")

    # --- PRODUCTION TABS LAYOUT ---
    tab_monitoring, tab_physics = st.tabs(["📺 SCADA Live Monitoring", "🔬 Advanced Physical Analytics"])

    # TAB 1: Core SCADA Telemetry
    with tab_monitoring:
        st.subheader("🔋 Battery Management System (BMS)")
        col_bat1, col_bat2 = st.columns(2)
        with col_bat1:
            chart_voltage.render(df_bat_filtered)
        with col_bat2:
            chart_temperature.render(df_bat_filtered)

        st.markdown("---")
        st.subheader("⚡ Power Conversion System (PCS) & Environment")
        col_inv1, col_inv2 = st.columns(2)
        with col_inv1:
            chart_inverter.render(df_env, df_inv)
        with col_inv2:
            chart_hvac.render(df_env)

    # TAB 2: Engineering & Degradation Diagnostics
    with tab_physics:
        st.subheader("🔬 Performance Degradation & Thermal Diagnostics")
        chart_soe.render(df_inv, physics_engine.dt_hours)

        st.markdown("---")
        col_an1, col_an2 = st.columns(2)
        with col_an1:
            chart_delta_t.render(df_delta_t)
        with col_an2:
            chart_resistance.render(df_res_data)