from abc import ABC, abstractmethod

import pandas as pd


class BESSBaseChart(ABC):
    """Abstract base class establishing a unified high-contrast SCADA palette and rendering interface"""

    def __init__(self):
        # Standardized enterprise SCADA high-contrast color scheme mapped to shortened IDs
        self.color_palette = {
            "bat1": "#1f77b4",
            "bat2": "#FF4B4B",
            "bat3": "#2ca02c",
            "bat4": "#FF00F0",
            "bat5": "#FFAA00",
        }

    @abstractmethod
    def render(self, *dfs: pd.DataFrame) -> None:
        """Polymorphic entry point to compile and display the targeted Plotly figure object"""
        pass
