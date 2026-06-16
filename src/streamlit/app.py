"""
BESS Real-Time Diagnostic Dashboard
"""

import os
import sys

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.analytics.physics_analytics import BESSPhysicsAnalytics
from src.streamlit.data_loader import BESSDataLoader
from src.streamlit.tabs.tab_business import render_business_tab

from src.streamlit.tabs.tab_monitoring import render_monitoring_tab
from src.streamlit.tabs.tab_physics import render_physics_tab
from src.streamlit.tabs.tab_weather import render_weather_tab
from src.streamlit.ui_components import render_hardware_filters, render_kpi_panel, render_sidebar_config

# === PAGE CONFIGURATION ===
# Configure Streamlit page settings (must be first Streamlit command)
st.set_page_config(
    page_title="BESS Telemetry Dashboard",  # Browser tab title
    page_icon="🔋",  # Browser tab icon (emoji or file path)
    layout="wide",  # Use full screen width (vs. centered)
)

st.title("🔋 BESS Real-Time Diagnostic Dashboard")


@st.cache_resource
def init_services():

    data_dir = os.getenv("DATA_DIR", "./data")
    return (BESSDataLoader(base_dir=data_dir), BESSPhysicsAnalytics(sampling_interval_minutes=10.0))


data_loader, physics_engine = init_services()
selected_date_str = render_sidebar_config(data_loader)


# === DATA LOADING WITH CACHING ===
@st.cache_data(ttl=60)
def load_all_data(date_str: str):

    environment_df, inverter_df, battery_df = data_loader.load_daily_data(date_str)
    market_df = data_loader.load_processed_file("processed/market_analytics", date_str)
    weather_df = data_loader.load_processed_file("processed/weather_analytics", date_str)
    return environment_df, inverter_df, battery_df, market_df, weather_df


environment_df, inverter_df, battery_df, market_df, weather_df = load_all_data(selected_date_str)


# === MAIN APPLICATION LOGIC ===
# Check if critical telemetry data loaded successfully
# all(): Returns True only if all values are not None
if all(v is not None for v in [environment_df, inverter_df, battery_df]):
    # === HARDWARE FILTERING ===
    # Apply user-selected hardware filters (racks and modules)
    # battery_filtered_df: Subset of battery data matching user selection
    battery_filtered_df = render_hardware_filters(battery_df)

    # Check if filtering resulted in empty dataset
    if battery_filtered_df.empty:
        # No hardware selected: Display warning and stop
        st.warning("⚠️ All hardware assets deselected. Please select at least one module.")
        st.stop()

    # === PRE-COMPUTE ANALYTICS ===
    # Run physics computations once before tab rendering
    # Avoids redundant calculations if data used in multiple tabs

    # metrics: Dictionary with RTE and energy throughput
    # Keys: 'rte_percent', 'total_charged_MWh', 'total_discharged_MWh'
    metrics = physics_engine.calculate_energy_and_rte(inverter_df)

    # temperature_delta_df: Thermal delta calculations across racks
    # Columns: timestamp, rack_id, max, min, delta_t_C
    temperature_delta_df = physics_engine.calculate_temperature_delta(battery_filtered_df)

    # resistance_data_df: High-current data for resistance estimation
    # Filtered to |current| > 5A for meaningful analysis
    resistance_data_df = physics_engine.estimate_internal_resistance_data(battery_filtered_df)

    # === TOP KPI PANEL ===
    # Display key performance indicators above tabs
    render_kpi_panel(environment_df, metrics)

    # === TABS NAVIGATION ===
    # Create tabbed interface for different analysis views
    # tabs: List of tab objects for content rendering
    tabs = st.tabs(
        [
            "📺 SCADA Live Monitoring",  # Tab 0: Real-time telemetry
            "🔬 Advanced Physical Analytics",  # Tab 1: Physics deep dive
            "🌤️ Weather Forecast",  # Tab 2: Solar PV forecasts
            "📈 Business Strategy",  # Tab 3: Market recommendations
        ]
    )

    # === TAB 0: SCADA MONITORING ===
    with tabs[0]:
        # Render real-time monitoring tab
        # Shows: Current status, telemetry charts, system overview
        render_monitoring_tab(battery_filtered_df, environment_df, inverter_df)

    # === TAB 1: PHYSICS ANALYTICS ===
    with tabs[1]:
        # Render physics analytics tab
        # Shows: Efficiency, thermal analysis, resistance, degradation
        render_physics_tab(
            inverter_df, temperature_delta_df, resistance_data_df, physics_engine.sampling_interval_hours
        )

    # === TAB 2: WEATHER FORECAST ===
    with tabs[2]:
        # Check if weather data available
        if weather_df is not None and not weather_df.empty:
            # Render weather forecast tab
            # Shows: Solar radiation, cloud cover, PV generation estimates
            render_weather_tab(weather_df)
        else:
            # Weather data not available
            st.error("Weather analytics data not found.")

    # === TAB 3: BUSINESS STRATEGY ===
    with tabs[3]:
        # Check if both market and weather data available
        if market_df is not None and not market_df.empty and weather_df is not None and not weather_df.empty:
            # Render business strategy tab
            # Shows: Market prices, charge/discharge recommendations, revenue optimization
            render_business_tab(market_df, weather_df)
        else:
            # One or both analytics datasets missing
            st.error("Market or weather analytics data not found.")
