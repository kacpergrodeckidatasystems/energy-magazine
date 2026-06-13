"""
BESS Real-Time Diagnostic Dashboard

This is the main entry point for the Streamlit-based Battery Energy Storage System
(BESS) monitoring and analytics dashboard application. It orchestrates data loading,
analytics processing, and multi-tab visualization for comprehensive BESS monitoring.

Application Purpose:
    Provide real-time operational visibility and analytics for BESS operators,
    enabling data-driven decisions for performance optimization, maintenance
    planning, and revenue maximization.

Main Features:
    1. SCADA-style Real-Time Monitoring:
       - Live telemetry visualization
       - System status indicators
       - Anomaly detection and alerts

    2. Advanced Physics Analytics:
       - Round-trip efficiency calculations
       - Thermal delta analysis
       - Internal resistance estimation
       - Degradation tracking

    3. Weather Forecast Integration:
       - Solar PV generation estimates
       - Cloud cover impact analysis
       - Multi-day forecast visualization

    4. Business Strategy Recommendations:
       - Market price-based charge/discharge decisions
       - Revenue optimization suggestions
       - Energy arbitrage analysis

Application Architecture:
    ┌─────────────────────────────────────────────────┐
    │                   app.py                        │
    │              (Orchestration Layer)              │
    ├─────────────────────────────────────────────────┤
    │                                                 │
    │  ┌──────────────┐  ┌──────────────────────┐   │
    │  │ Data Loader  │  │ Physics Analytics    │   │
    │  │   (SRP)      │  │      Engine          │   │
    │  └──────────────┘  └──────────────────────┘   │
    │                                                 │
    │  ┌──────────────────────────────────────────┐  │
    │  │        UI Components                     │  │
    │  │  - Sidebar Config                        │  │
    │  │  - Hardware Filters                      │  │
    │  │  - KPI Panel                             │  │
    │  └──────────────────────────────────────────┘  │
    │                                                 │
    │  ┌──────────────────────────────────────────┐  │
    │  │           Tab Renderers                  │  │
    │  │  - Monitoring  - Physics                 │  │
    │  │  - Weather     - Business                │  │
    │  └──────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────┘

Design Principles:
    - Separation of Concerns: Data, logic, and presentation layers separated
    - Caching Strategy: Resource caching for services, data caching with TTL
    - Defensive Programming: Null checks and error handling throughout
    - User Experience: Clear messages, responsive UI, intuitive navigation

Technology Stack:
    - Streamlit: Web application framework
    - Pandas: Data manipulation and analysis
    - Plotly: Interactive visualizations (in tab modules)
    - Custom modules: Domain-specific analytics

Configuration:
    - Page Title: "BESS Telemetry Dashboard"
    - Page Icon: 🔋
    - Layout: Wide (utilizes full screen width)
    - Data Directory: Configurable via DATA_DIR env variable

Execution Flow:
    1. Initialize services (data loader, physics engine)
    2. Render sidebar configuration (date selection)
    3. Load all data for selected date (with caching)
    4. Apply hardware filters based on user selection
    5. Pre-compute physics analytics
    6. Render KPI panel with key metrics
    7. Render tabbed interface with specialized views
    8. Each tab independently visualizes relevant data

Caching Strategy:
    - @st.cache_resource: Services (data loader, analytics engine)
      Benefits: Persist across reruns, shared across users

    - @st.cache_data(ttl=60): Data loading
      Benefits: Fast repeated access, 60-second refresh for near real-time

Error Handling:
    - Missing data: Stops execution with clear message
    - Empty filters: Warning message guides user
    - Missing analytics: Tab-level error messages

Performance Optimizations:
    - Service initialization cached
    - Data loading cached with TTL
    - Physics computations run once before tabs
    - Hardware filtering applied early
    - Efficient parquet format for storage

User Workflow:
    1. User opens dashboard in browser
    2. Selects analysis date from sidebar
    3. Optionally filters hardware (racks/modules)
    4. Views KPIs at top of page
    5. Navigates between tabs for different analyses:
       - Monitoring: Real-time SCADA view
       - Physics: Deep analytics and efficiency
       - Weather: Solar forecasts and impacts
       - Business: Market strategy recommendations

Environment Variables:
    DATA_DIR: Base directory for data files
              Default: "./data"
              Production: "/opt/airflow/data"

Dependencies:
    Core:
    - streamlit: UI framework
    - pandas: Data processing
    - os, sys: System operations

    Custom Modules:
    - data_loader: Data access layer
    - physics_analytics: Analytics engine
    - ui_components: Reusable UI elements
    - tab_*: Tab-specific rendering modules

Author: BESS Operations Team
Version: 1.0.0
Last Modified: 2026-06-13
"""

import os
import sys

import streamlit as st

# Ensure project root is in Python path for module imports
# This allows imports like "from src.streamlit..." to work
# Navigates up two levels from this file's location to project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import core services and components
from src.analytics.physics_analytics import BESSPhysicsAnalytics
from src.streamlit.data_loader import BESSDataLoader
from src.streamlit.tabs.tab_business import render_business_tab

# Import tab rendering modules
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

# Display main application title with icon
st.title("🔋 BESS Real-Time Diagnostic Dashboard")


# === SERVICE INITIALIZATION ===
@st.cache_resource
def init_services():
    """
    Initialize and cache application services.

    Creates singleton instances of core services that persist across Streamlit
    reruns and are shared across all user sessions. This optimization prevents
    redundant initialization and improves application performance.

    Services Initialized:
        1. BESSDataLoader: Data access layer for loading telemetry
        2. BESSPhysicsAnalytics: Physics computation engine

    Caching Strategy:
        @st.cache_resource: Resource-level caching
        - Persists across reruns (button clicks, interactions)
        - Shared across user sessions (memory efficient)
        - Never expires (services are stateless)
        - Ideal for: Database connections, ML models, API clients

    Configuration:
        data_dir: Read from DATA_DIR environment variable
                 Default: "./data" (development)
                 Production: "/opt/airflow/data" or similar

        sampling_interval: 10.0 minutes (matches data generation)
                          Used in energy integration calculations

    Returns:
        tuple: (data_loader, physics_engine)
            - data_loader (BESSDataLoader): Configured data access object
            - physics_engine (BESSPhysicsAnalytics): Configured analytics engine

    Example:
        >>> # First call: Creates instances
        >>> loader, engine = init_services()
        >>>
        >>> # Subsequent calls: Returns cached instances
        >>> loader2, engine2 = init_services()
        >>> loader is loader2  # Same object
        True

    Note:
        - Called once per application lifecycle
        - Services are stateless (safe to share)
        - Configuration read from environment
        - No cleanup needed (stateless services)
    """
    # Read data directory from environment variable
    # Default to "./data" for local development
    data_dir = os.getenv("DATA_DIR", "./data")

    # Create and return service instances
    return (BESSDataLoader(base_dir=data_dir), BESSPhysicsAnalytics(sampling_interval_minutes=10.0))


# Initialize services (cached)
# data_loader: Instance for loading telemetry data
# physics_engine: Instance for physics calculations
data_loader, physics_engine = init_services()


# === SIDEBAR & USER CONFIGURATION ===
# Render sidebar date selection interface
# selected_date_str: User-selected date in YYYYMMDD format (e.g., "20240613")
# This function may call st.stop() if no data available
selected_date_str = render_sidebar_config(data_loader)


# === DATA LOADING WITH CACHING ===
@st.cache_data(ttl=60)
def load_all_data(date_str: str):
    """
    Load all telemetry and analytics data for the selected date.

    Orchestrates loading of raw telemetry (environment, inverter, battery)
    and processed analytics (market, weather) for a specific date. Results
    are cached with a 60-second TTL to balance performance and freshness.

    Caching Strategy:
        @st.cache_data(ttl=60): Data-level caching with Time-To-Live
        - Cache expires after 60 seconds
        - Allows near real-time updates when DAG runs complete
        - Cache key includes date_str (separate cache per date)
        - Safe for data that may change over time

    Loading Sequence:
        1. Load raw telemetry:
           - Environment sensors
           - Inverter performance
           - Battery BMS data

        2. Load processed analytics:
           - Market price recommendations
           - Weather PV forecasts

    Args:
        date_str (str): Date in YYYYMMDD format for data loading.
                       Example: "20240613"

    Returns:
        tuple: (df_env, df_inv, df_bat, df_market, df_weather)

            df_env (pd.DataFrame): Environment telemetry
                                  Columns: timestamp, temp sensors, solar, grid
                                  Records: ~144 (24 hours / 10 minutes)

            df_inv (pd.DataFrame): Inverter performance data
                                  Columns: timestamp, efficiency, power
                                  Records: ~144

            df_bat (pd.DataFrame): Battery BMS data
                                  Columns: timestamp, rack_id, module_id, voltage,
                                          current, temperature, SOC
                                  Records: ~1440 (144 × 10 modules)

            df_market (pd.DataFrame): Market analytics
                                     Columns: timestamp, price, recommendation
                                     Records: 24-48 (hourly or 15-min)
                                     Empty DataFrame if file not found

            df_weather (pd.DataFrame): Weather analytics
                                      Columns: timestamp, radiation, cloud cover,
                                              estimated_power_kw
                                      Records: 48 (hourly, 2-day forecast)
                                      Empty DataFrame if file not found

    Example:
        >>> # First call: Loads from disk
        >>> data = load_all_data("20240613")
        >>> # Processing time: ~100-300ms
        >>>
        >>> # Subsequent calls within 60s: Returns cached data
        >>> data = load_all_data("20240613")
        >>> # Processing time: ~1ms (cache hit)
        >>>
        >>> # After 60 seconds: Reloads from disk
        >>> data = load_all_data("20240613")
        >>> # Processing time: ~100-300ms (cache expired)

    Cache Behavior:
        - Separate cache entry for each date_str
        - Cache shared across all users
        - Automatic invalidation after 60 seconds
        - Manual invalidation: Clear cache button in Streamlit UI

    Error Handling:
        - Telemetry errors: Handled by data_loader (returns None)
        - Analytics errors: Handled by data_loader (returns empty DataFrame)
        - Caller must check for None/empty before use

    Performance:
        - Cache hit: ~1ms (memory access)
        - Cache miss: ~100-300ms (disk read + parquet parsing)
        - Memory usage: ~5-10 MB per date cached

    TTL Rationale:
        - 60 seconds balances freshness and performance
        - Airflow DAGs typically run every 15-60 minutes
        - Multiple users benefit from shared cache
        - Automatic refresh prevents stale data

    Note:
        - Empty DataFrames indicate missing analytics (not error)
        - None values indicate critical telemetry load failure
        - Cache size grows with unique dates accessed
        - Streamlit automatically manages cache memory
    """
    # Load raw telemetry data for selected date
    # env, inv, bat: Main telemetry DataFrames or None on error
    env, inv, bat = data_loader.load_daily_data(date_str)

    # Load processed analytics files
    # market: Market analytics or empty DataFrame if not found
    market = data_loader.load_processed_file("processed/market_analytics", date_str)

    # weather: Weather analytics or empty DataFrame if not found
    weather = data_loader.load_processed_file("processed/weather_analytics", date_str)

    # Return all loaded data as tuple
    return env, inv, bat, market, weather


# Load all data for selected date (cached)
# Unpack tuple into individual DataFrames
df_env, df_inv, df_bat, df_market, df_weather = load_all_data(selected_date_str)


# === MAIN APPLICATION LOGIC ===
# Check if critical telemetry data loaded successfully
# all(): Returns True only if all values are not None
if all(v is not None for v in [df_env, df_inv, df_bat]):
    # === HARDWARE FILTERING ===
    # Apply user-selected hardware filters (racks and modules)
    # df_bat_filtered: Subset of battery data matching user selection
    df_bat_filtered = render_hardware_filters(df_bat)

    # Check if filtering resulted in empty dataset
    if df_bat_filtered.empty:
        # No hardware selected: Display warning and stop
        st.warning("⚠️ All hardware assets deselected. Please select at least one module.")
        st.stop()

    # === PRE-COMPUTE ANALYTICS ===
    # Run physics computations once before tab rendering
    # Avoids redundant calculations if data used in multiple tabs

    # metrics: Dictionary with RTE and energy throughput
    # Keys: 'rte_percent', 'total_charged_MWh', 'total_discharged_MWh'
    metrics = physics_engine.calculate_energy_and_rte(df_inv)

    # df_delta_t: Thermal delta calculations across racks
    # Columns: timestamp, rack_id, max, min, delta_t_C
    df_delta_t = physics_engine.calculate_delta_t(df_bat_filtered)

    # df_res_data: High-current data for resistance estimation
    # Filtered to |current| > 5A for meaningful analysis
    df_res_data = physics_engine.estimate_internal_resistance_data(df_bat_filtered)

    # === TOP KPI PANEL ===
    # Display key performance indicators above tabs
    render_kpi_panel(df_env, metrics)

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
        render_monitoring_tab(df_bat_filtered, df_env, df_inv)

    # === TAB 1: PHYSICS ANALYTICS ===
    with tabs[1]:
        # Render physics analytics tab
        # Shows: Efficiency, thermal analysis, resistance, degradation
        render_physics_tab(df_inv, df_delta_t, df_res_data, physics_engine.dt_hours)

    # === TAB 2: WEATHER FORECAST ===
    with tabs[2]:
        # Check if weather data available
        if df_weather is not None and not df_weather.empty:
            # Render weather forecast tab
            # Shows: Solar radiation, cloud cover, PV generation estimates
            render_weather_tab(df_weather)
        else:
            # Weather data not available
            st.error("Weather analytics data not found.")

    # === TAB 3: BUSINESS STRATEGY ===
    with tabs[3]:
        # Check if both market and weather data available
        if df_market is not None and not df_market.empty and df_weather is not None and not df_weather.empty:
            # Render business strategy tab
            # Shows: Market prices, charge/discharge recommendations, revenue optimization
            render_business_tab(df_market, df_weather)
        else:
            # One or both analytics datasets missing
            st.error("Market or weather analytics data not found.")

# If we reach here without entering the if block, telemetry loading failed
# Error message already shown by data_loader.load_daily_data()
# Application gracefully stops without rendering content
