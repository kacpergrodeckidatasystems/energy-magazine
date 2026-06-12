import logging
import streamlit as st
import pandas as pd
import plotly.express as px
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_weather_tab(df_weather: pd.DataFrame) -> None:
    """
    Renders the Weather Forecast and PV Generation capacity tab.
    
    Args:
        df_weather (pd.DataFrame): Processed weather analytics dataframe.
    """
    st.subheader("🌤️ Weather & Solar Generation Forecast")
    
    # --- Top Level Metrics ---
    logger.info("Rendering Weather Tab...")
    
    # Walidacja kolumn przed renderowaniem (dobre miejsce na logowanie błędów)
    required_columns = ['temperature_2m', 'global_radiation', 'estimated_power_kw']
    if not all(col in df_weather.columns for col in required_columns):
        logger.error(f"Missing columns in df_weather. Found: {df_weather.columns.tolist()}")
        st.error("Data processing error: Missing metrics.")
        return

    st.subheader("🌤️ Weather & Solar Generation Forecast")
    
    # --- Top Level Metrics ---
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Max Temperature", f"{df_weather['temperature_2m'].max():.1f} °C")
    col2.metric("Peak Solar Radiation", f"{df_weather['global_radiation'].max():.0f} W/m²")
    col3.metric("Peak Est. PV Power", f"{df_weather['estimated_power_kw'].max():.1f} kW")
    
    st.markdown("---")
    
    # --- Charts Layout ---
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("**Thermal & Environmental Outlook**")
        fig_temp = px.line(
            df_weather, 
            x="timestamp", 
            y="temperature_2m", 
            title="Temperature Forecast (°C)",
            color_discrete_sequence=["#29b5e8"]
        )
        fig_temp.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_temp, use_container_width=True)
        
    with chart_col2:
        st.markdown("**Estimated PV Generation Capacity**")
        fig_pv = px.area(
            df_weather, 
            x="timestamp", 
            y="estimated_power_kw", 
            title="Available Solar Power (kW)", 
            color_discrete_sequence=["#FFA15A"]
        )
        fig_pv.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pv, use_container_width=True)