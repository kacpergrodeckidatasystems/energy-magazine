import streamlit as st
import pandas as pd
import plotly.express as px

def _get_top_recommendations(df_market: pd.DataFrame, df_weather: pd.DataFrame) -> list:
    """
    Evaluates market and weather conditions to generate top 2 operational strategies.
    """
    min_price = df_market['price_eur_mwh'].min()
    max_price = df_market['price_eur_mwh'].max()
    max_temp = df_weather['temperature_2m'].max()
    max_solar = df_weather['global_radiation'].max()
    
    recommendations_pool = {
        "REC_01": "GRID CHARGE OPPORTUNITY: Negative prices detected. Maximize charging from the grid.",
        "REC_02": "PEAK DISCHARGE: Severe evening price peaks detected. Prepare BESS for maximum export.",
        "REC_03": "SOLAR STORAGE MODE: High solar generation with low market prices. Store excess PV energy.",
        "REC_04": "BYPASS TO GRID: High PV generation coincides with high market prices. Export PV directly.",
        "REC_05": "STANDBY: Prices are stable and PV yield is moderate. Keep BESS in standby to avoid cycling.",
        "REC_06": "THERMAL WARNING: High temperatures detected (>30°C). Engage HVAC cooling systems.",
        "REC_08": "INTRADAY ARBITRAGE: High volatility (large spread). Execute rapid charge/discharge cycles."
    }
    
    active_recs = []
    
    if min_price < 0:
        active_recs.append(recommendations_pool["REC_01"])
    if max_price > 300:
        active_recs.append(recommendations_pool["REC_02"])
    if max_solar > 700 and min_price < 50:
        active_recs.append(recommendations_pool["REC_03"])
    if max_temp > 30:
        active_recs.append(recommendations_pool["REC_06"])
    if (max_price - min_price) > 200:
        active_recs.append(recommendations_pool["REC_08"])
        
    if not active_recs:
        active_recs.append(recommendations_pool["REC_05"])
        
    return active_recs[:2]

def render_business_tab(df_market: pd.DataFrame, df_weather: pd.DataFrame) -> None:
    """
    Renders the Business Analytics and Strategy Recommendations tab.
    
    Args:
        df_market (pd.DataFrame): Processed market prices dataframe.
        df_weather (pd.DataFrame): Processed weather analytics dataframe.
    """
    st.subheader("📈 Market Economics & Trading Strategy")
    
    # --- Market Chart ---
    fig_price = px.line(
        df_market, 
        x="timestamp", 
        y="price_eur_mwh", 
        title="Day-Ahead Market Prices (EUR/MWh)",
        color_discrete_sequence=["#FF4B4B"]
    )
    # Add a zero-line reference for negative prices
    fig_price.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
    fig_price.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_price, use_container_width=True)
    
    st.divider()
    
    # --- AI Recommendations ---
    st.subheader("💡 Automated Strategy Recommendations")
    st.caption("Derived from combined 24h weather and market volatility predictions.")
    
    top_actions = _get_top_recommendations(df_market, df_weather)
    
    for i, action in enumerate(top_actions):
        if "WARNING" in action or "RISK" in action:
            st.warning(f"**Action {i+1}:** {action}")
        elif "CHARGE" in action or "DISCHARGE" in action or "ARBITRAGE" in action:
            st.success(f"**Action {i+1}:** {action}")
        else:
            st.info(f"**Action {i+1}:** {action}")