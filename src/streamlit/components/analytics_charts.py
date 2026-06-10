import pandas as pd
import plotly.express as px

import streamlit as st
from src.streamlit.components.base_chart import BESSBaseChart


class EnergyStateOfEnergyChart(BESSBaseChart):
    """Area chart displaying integrated historical cumulative state of energy (SoE)"""

    def render(self, df_inv: pd.DataFrame, dt_hours: float) -> None:
        discharged = df_inv["active_power_output_MW"].apply(lambda x: x * dt_hours if x > 0 else 0)
        charged = df_inv["active_power_output_MW"].apply(lambda x: abs(x) * dt_hours if x < 0 else 0)
        df_inv["bess_soe_MWh"] = (charged - discharged).cumsum()

        fig = px.area(
            df_inv,
            x="timestamp",
            y="bess_soe_MWh",
            title="BESS Energy Capacity Profile (SoE)",
            labels={"bess_soe_MWh": "Energy (MWh)", "timestamp": "Time"},
            color_discrete_sequence=["#00CC96"],
        )
        fig.update_layout(template="plotly_dark", margin=dict(l=40, r=40, t=50, b=40))
        st.plotly_chart(fig, width="stretch")


class ThermalDeltaTChart(BESSBaseChart):
    """Line chart tracking multi-rack cell temperature dispersion limits"""

    def render(self, df_delta_t: pd.DataFrame) -> None:
        fig = px.line(
            df_delta_t,
            x="timestamp",
            y="delta_t_C",
            color="rack_id",
            title="Rack Thermal Balancing Dispersion (Delta T)",
            labels={"delta_t_C": "Delta T (°C)", "timestamp": "Time", "rack_id": "Rack Unit"},
        )
        fig.add_hline(
            y=5.0,
            line_dash="dash",
            line_color="#FF4B4B",
            annotation_text="Degradation Limit (5°C)",
            annotation_position="top left",
        )
        fig.update_layout(
            template="plotly_dark",
            legend_orientation="h",
            legend=dict(yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=60, b=40),
        )
        st.plotly_chart(fig, width="stretch")


class InternalResistanceScatterChart(BESSBaseChart):
    """Faceted cross-correlation matrix mapping U vs I slope characteristics"""

    def render(self, df_res: pd.DataFrame) -> None:
        fig = px.scatter(
            df_res,
            x="rack_total_current_A",
            y="module_voltage_V",
            color="battery_module_id",
            facet_col="rack_id",
            title="Current-Voltage Characteristic Matrix (R_int Estimate)",
            labels={
                "rack_total_current_A": "Current (A)",
                "module_voltage_V": "Voltage (V)",
                "battery_module_id": "Module",
            },
            color_discrete_map=self.color_palette,
        )
        fig.update_layout(
            template="plotly_dark",
            legend_orientation="h",
            legend=dict(yanchor="bottom", y=1.12, xanchor="center", x=0.5),
            margin=dict(l=40, r=40, t=80, b=40),
        )
        # Custom clean-up for the facet graph sub-headers
        fig.for_each_annotation(lambda a: a.update(text=a.text.replace("rack_id=", "Rack: ")))
        st.plotly_chart(fig, width="stretch")
