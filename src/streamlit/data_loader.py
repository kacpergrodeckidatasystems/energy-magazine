import logging
import os

import pandas as pd

import streamlit as st

logger = logging.getLogger(__name__)


class BESSDataLoader:
    def __init__(self, base_dir: str = "./data"):

        self.base_dir = base_dir
        self.environment_dir = os.path.join(base_dir, "environment")
        self.inverter_dir = os.path.join(base_dir, "inverter")
        self.battery_dir = os.path.join(base_dir, "battery")

    def get_available_dates(self) -> list:
        if not os.path.exists(self.environment_dir):
            return []

        files = [f for f in os.listdir(self.environment_dir) if f.startswith("env_") and f.endswith(".parquet")]

        return sorted([f.split("_")[1].split(".")[0] for f in files])

    def load_daily_data(self, date_str: str) -> tuple:

        try:
            environment_df = pd.read_parquet(os.path.join(self.environment_dir, f"env_{date_str}.parquet")).sort_values(
                "timestamp"
            )
            inverter_df = pd.read_parquet(os.path.join(self.inverter_dir, f"inv_{date_str}.parquet")).sort_values(
                "timestamp"
            )
            battery_df = pd.read_parquet(os.path.join(self.battery_dir, f"bat_{date_str}.parquet")).sort_values(
                "timestamp"
            )

            if "battery_module_id" in battery_df.columns:
                battery_df["battery_module_id"] = battery_df["battery_module_id"].str.replace("battery_module_0", "bat")

            return environment_df, inverter_df, battery_df

        except Exception as e:
            st.error(f"Critical error loading daily telemetry data: {str(e)}")
            logger.error(f"Failed to load daily data for {date_str}: {str(e)}", exc_info=True)
            return None, None, None

    def load_processed_file(self, file_type: str, date_str: str) -> pd.DataFrame:

        file_path = os.path.join(self.base_dir, "raw", f"{file_type}.parquet")
        logger.info(f"Trying to load file from: {file_path}")
        if os.path.exists(file_path):
            # File exists: Load and return DataFrame
            return pd.read_parquet(file_path)

        return pd.DataFrame()
