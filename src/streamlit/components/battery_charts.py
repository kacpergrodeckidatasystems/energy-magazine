import pandas as pd
import plotly.express as px

import streamlit as st
from src.streamlit.components.base_chart import BESSBaseChart


class BatteryVoltageChart(BESSBaseChart):
    """Line chart tracking multi-rack cell voltage profiles and cross-unit imbalances"""

    def render(self, df_bat: pd.DataFrame) -> None:
        fig = px.line(
            df_bat,
            x="timestamp",
            y="module_voltage_V",
            color="battery_module_id",
            facet_col="rack_id" if len(df_bat["rack_id"].unique()) > 1 else None,
            title="Module Voltage Telemetry",
            labels={"module_voltage_V": "Voltage (V)", "timestamp": "Time", "battery_module_id": "Module"},
            color_discrete_map=self.color_palette,
        )
        fig.update_layout(template="plotly_dark", legend_orientation="h", margin=dict(l=40, r=40, t=50, b=40))
        if len(df_bat["rack_id"].unique()) > 1:
            fig.for_each_annotation(lambda a: a.update(text=a.text.replace("rack_id=", "Rack: ")))
        st.plotly_chart(fig, width="stretch")


class BatteryTemperatureChart(BESSBaseChart):
    """Line chart tracking multi-rack cell thermal layers and safe operating envelopes"""

    def render(self, df_bat: pd.DataFrame) -> None:
        fig = px.line(
            df_bat,
            x="timestamp",
            y="module_temperature_C",
            color="battery_module_id",
            facet_col="rack_id" if len(df_bat["rack_id"].unique()) > 1 else None,
            title="Module Thermal Telemetry",
            labels={"module_temperature_C": "Temperature (°C)", "timestamp": "Time", "battery_module_id": "Module"},
            color_discrete_map=self.color_palette,
        )
        fig.update_layout(template="plotly_dark", legend_orientation="h", margin=dict(l=40, r=40, t=50, b=40))
        if len(df_bat["rack_id"].unique()) > 1:
            fig.for_each_annotation(lambda a: a.update(text=a.text.replace("rack_id=", "Rack: ")))
        st.plotly_chart(fig, width="stretch")
