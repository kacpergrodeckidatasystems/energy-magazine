"""
Weather & Solar Generation Tab Module
======================================

This module provides the weather forecast and photovoltaic (PV) generation
visualization tab for the BESS Analytics Dashboard. It displays:
  - Temperature forecasts from weather APIs
  - Global solar radiation measurements
  - Estimated PV power generation capacity

The tab helps operators understand environmental conditions that affect:
  - Solar charging potential for battery systems
  - Thermal constraints on battery operations
  - Day-ahead energy arbitrage planning

Dependencies:
    - streamlit: Web UI framework
    - pandas: Data manipulation and analysis
    - plotly: Interactive charting library

Author: BESS Analytics Team
"""

import logging

import pandas as pd
import plotly.express as px

import streamlit as st

# Configure logging for debugging and operational monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def render_weather_tab(df_weather: pd.DataFrame) -> None:
    """
    Render the Weather Forecast and PV Generation capacity visualization tab.

    This function creates an interactive dashboard section displaying weather
    forecasts and estimated solar power generation. It includes:
      - Top-level metrics: max temperature, peak radiation, peak PV power
      - Time-series temperature forecast chart
      - Time-series estimated PV generation chart

    Args:
        df_weather (pd.DataFrame): Processed weather analytics dataframe containing:
            - timestamp: Datetime index for forecast periods
            - temperature_2m: Temperature forecast in Celsius
            - global_radiation: Solar radiation in W/m²
            - estimated_power_kw: Estimated PV power generation in kW

    Returns:
        None: Renders directly to Streamlit UI

    Raises:
        Logs an error and displays user-friendly message if required columns
        are missing from the input dataframe.

    Example:
        >>> df = pd.DataFrame({
        ...     'timestamp': pd.date_range('2024-01-01', periods=24, freq='H'),
        ...     'temperature_2m': np.random.uniform(10, 25, 24),
        ...     'global_radiation': np.random.uniform(0, 800, 24),
        ...     'estimated_power_kw': np.random.uniform(0, 5, 24)
        ... })
        >>> render_weather_tab(df)
    """
    st.subheader("🌤️ Weather & Solar Generation Forecast")

    logger.info("Rendering Weather Tab...")

    # --- DATA VALIDATION ---
    # Ensure all required columns exist before attempting visualization
    required_columns = ["temperature_2m", "global_radiation", "estimated_power_kw"]
    if not all(col in df_weather.columns for col in required_columns):
        logger.error(f"Missing columns in df_weather. Found: {df_weather.columns.tolist()}")
        st.error("⚠️ Data processing error: Missing required weather metrics.")
        return

    # --- TOP LEVEL METRICS ---
    # Display key summary statistics at the top for quick operational overview
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Max Temperature",
        f"{df_weather['temperature_2m'].max():.1f} °C",
        help="Maximum forecasted temperature (affects battery thermal limits)",
    )
    col2.metric(
        "Peak Solar Radiation",
        f"{df_weather['global_radiation'].max():.0f} W/m²",
        help="Peak global horizontal irradiance (GHI) in Watts per square meter",
    )
    col3.metric(
        "Peak Est. PV Power",
        f"{df_weather['estimated_power_kw'].max():.1f} kW",
        help="Maximum estimated photovoltaic generation capacity",
    )

    st.markdown("---")  # Visual separator

    # --- TIME-SERIES CHARTS LAYOUT ---
    # Display two side-by-side charts for detailed forecast analysis
    chart_col1, chart_col2 = st.columns(2)

    # LEFT CHART: Temperature Forecast
    with chart_col1:
        st.markdown("**🌡️ Thermal & Environmental Outlook**")
        fig_temp = px.line(
            df_weather,
            x="timestamp",
            y="temperature_2m",
            title="Temperature Forecast (°C)",
            color_discrete_sequence=["#29b5e8"],  # Light blue color theme
        )
        fig_temp.update_layout(
            template="plotly_dark",  # Dark theme for better visibility
            margin=dict(l=20, r=20, t=40, b=20),  # Compact margins
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
        )
        st.plotly_chart(fig_temp, use_container_width=True)

    # RIGHT CHART: PV Power Generation Estimate
    with chart_col2:
        st.markdown("**☀️ Estimated PV Generation Capacity**")
        fig_pv = px.area(
            df_weather,
            x="timestamp",
            y="estimated_power_kw",
            title="Available Solar Power (kW)",
            color_discrete_sequence=["#FFA15A"],  # Orange color theme
        )
        fig_pv.update_layout(
            template="plotly_dark",  # Dark theme for consistency
            margin=dict(l=20, r=20, t=40, b=20),  # Compact margins
            xaxis_title="Time",
            yaxis_title="Power (kW)",
        )
        st.plotly_chart(fig_pv, use_container_width=True)

    logger.info("Weather tab rendered successfully")
