import os

import pandas as pd

import streamlit as st


class BESSDataLoader:
    """Handles I/O operations for reading structured battery and system telemetry from the Bronze layer"""

    def __init__(self, base_dir: str = "./data/bronze"):
        self.env_dir = os.path.join(base_dir, "environment")
        self.inv_dir = os.path.join(base_dir, "inverter")
        self.bat_dir = os.path.join(base_dir, "battery")

    def get_available_dates(self) -> list:
        """Scans the environment path to dynamically fetch populated execution dates"""
        if not os.path.exists(self.env_dir):
            return []
        files = [f for f in os.listdir(self.env_dir) if f.startswith("env_") and f.endswith(".parquet")]
        return sorted([f.split("_")[1].split(".")[0] for f in files])

    def load_daily_data(self, date_str: str) -> tuple:
        """Loads and sorts historical whole-day telemetry from local Parquet storage into memory"""
        try:
            df_env = pd.read_parquet(os.path.join(self.env_dir, f"env_{date_str}.parquet")).sort_values("timestamp")
            df_inv = pd.read_parquet(os.path.join(self.inv_dir, f"inv_{date_str}.parquet")).sort_values("timestamp")
            df_bat = pd.read_parquet(os.path.join(self.bat_dir, f"bat_{date_str}.parquet")).sort_values("timestamp")

            # Production string optimization: battery_module_01 -> bat1
            if "battery_module_id" in df_bat.columns:
                df_bat["battery_module_id"] = df_bat["battery_module_id"].str.replace("battery_module_0", "bat")

            return df_env, df_inv, df_bat
        except Exception as e:
            st.error(f"Critical error loading Bronze tier telemetry matrix: {str(e)}")
            return None, None, None
