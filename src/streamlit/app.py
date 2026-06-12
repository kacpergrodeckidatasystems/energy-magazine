import os
import sys
import streamlit as st

# Ensure project root is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.streamlit.data_loader import BESSDataLoader
from src.analytics.physics_analytics import BESSPhysicsAnalytics
from src.streamlit.ui_components import render_sidebar_config, render_hardware_filters, render_kpi_panel

# Tab renderers
from src.streamlit.tabs.tab_monitoring import render_monitoring_tab
from src.streamlit.tabs.tab_physics import render_physics_tab
from src.streamlit.tabs.tab_weather import render_weather_tab
from src.streamlit.tabs.tab_business import render_business_tab

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="BESS Telemetry Dashboard", page_icon="🔋", layout="wide")
st.title("🔋 BESS Real-Time Diagnostic Dashboard")

# --- INITIALIZATION ---
@st.cache_resource
def init_services():
    data_dir = os.getenv("DATA_DIR", "./data")
    return BESSDataLoader(base_dir=data_dir), BESSPhysicsAnalytics(sampling_interval_minutes=10.0)

data_loader, physics_engine = init_services()

# --- SIDEBAR & DATA LOADING ---
selected_date_str = render_sidebar_config(data_loader)

@st.cache_data(ttl=60)
def load_all_data(date_str: str):

    env, inv, bat = data_loader.load_daily_data(date_str)
    
    market = data_loader.load_processed_file("processed/market_analytics", date_str)
    weather = data_loader.load_processed_file("processed/weather_analytics", date_str)
    
    return env, inv, bat, market, weather

df_env, df_inv, df_bat, df_market, df_weather = load_all_data(selected_date_str)

# --- MAIN EXECUTION ---
if all(v is not None for v in [df_env, df_inv, df_bat]):
    
    # Filter hardware
    df_bat_filtered = render_hardware_filters(df_bat)
    
    if df_bat_filtered.empty:
        st.warning("⚠️ All hardware assets deselected. Please select at least one module.")
        st.stop()

    # Pre-compute physics analytics
    metrics = physics_engine.calculate_energy_and_rte(df_inv)
    df_delta_t = physics_engine.calculate_delta_t(df_bat_filtered)
    df_res_data = physics_engine.estimate_internal_resistance_data(df_bat_filtered)

    # --- TOP KPI PANEL ---
    render_kpi_panel(df_env, metrics)

    # --- TABS ROUTING ---
    tabs = st.tabs([
        "📺 SCADA Live Monitoring", 
        "🔬 Advanced Physical Analytics",
        "🌤️ Weather Forecast",
        "📈 Business Strategy"
    ])

    with tabs[0]:
        render_monitoring_tab(df_bat_filtered, df_env, df_inv)

    with tabs[1]:
        render_physics_tab(df_inv, df_delta_t, df_res_data, physics_engine.dt_hours)

    with tabs[2]:
        if df_weather is not None:
            render_weather_tab(df_weather)
        else:
            st.error("Weather analytics data not found.")

    with tabs[3]:
        if df_market is not None and df_weather is not None:
            render_business_tab(df_market, df_weather)
        else:
            st.error("Market or weather analytics data not found.")