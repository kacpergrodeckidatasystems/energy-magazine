import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import streamlit as st
from src.streamlit.components.base_chart import BESSBaseChart


class InverterCorrelationChart(BESSBaseChart):
    """Dual-axis line chart correlating PCS active power profiles against solar irradiance trends"""

    def render(self, environment_df: pd.DataFrame, inverter_df: pd.DataFrame) -> None:
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=inverter_df["timestamp"],
                y=inverter_df["active_power_output_MW"],
                name="Active Power (MW)",
                mode="lines",
                line=dict(color="#00CC96", width=2),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=environment_df["timestamp"],
                y=environment_df["max_solar_radiation_W_m2"],
                name="Irradiance (W/m²)",
                mode="lines",
                line=dict(color="#FFA15A", dash="dot"),
                yaxis="y2",
            )
        )

        fig.update_layout(
            title="PCS Throughput vs Solar Irradiance Balance",
            template="plotly_dark",
            legend_orientation="h",
            yaxis=dict(title="Active Power (MW)"),
            yaxis2=dict(title="Solar Irradiance (W/m²)", overlaying="y", side="right"),
            margin=dict(l=40, r=40, t=50, b=40),
        )
        st.plotly_chart(fig, width="stretch")


class HvacSensorsChart(BESSBaseChart):
    """Line chart tracking internal container ambient temperature sensors and anomalies"""

    def render(self, environment_df: pd.DataFrame) -> None:
        df_melted = environment_df.melt(
            id_vars=["timestamp"],
            value_vars=[
                "ambient_temp_sensor_01_C",
                "ambient_temp_sensor_02_C",
                "ambient_temp_sensor_03_C",
                "ambient_temp_sensor_04_C_HIGH_ANOMALY",
                "ambient_temp_sensor_05_C_LOW_ANOMALY",
            ],
            var_name="Sensor",
            value_name="Temperature",
        )

        # Clean up string labels for professional SCADA legend rendering
        df_melted["Sensor"] = df_melted["Sensor"].str.replace("ambient_temp_sensor_", "S_").str.replace("_C", "")

        fig = px.line(
            df_melted,
            x="timestamp",
            y="Temperature",
            color="Sensor",
            title="Container Ambient Temperature Sensors",
            labels={"Temperature": "Temperature (°C)", "timestamp": "Time"},
        )
        fig.update_layout(template="plotly_dark", legend_orientation="h", margin=dict(l=40, r=40, t=50, b=40))
        st.plotly_chart(fig, width="stretch")
