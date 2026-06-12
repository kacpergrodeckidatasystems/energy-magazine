import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Importy Twoich funkcji z zakładek
from src.streamlit.tabs.tab_monitoring import render_monitoring_tab
from src.streamlit.tabs.tab_physics import render_physics_tab
from src.streamlit.tabs.tab_weather import render_weather_tab
from src.streamlit.tabs.tab_business import render_business_tab, _get_top_recommendations

# ==========================================
# FIXTURES (Przygotowanie danych testowych)
# ==========================================

@pytest.fixture
def mock_weather_df():
    """Zwraca DataFrame o strukturze wymaganej przez tab_weather i tab_business."""
    return pd.DataFrame({
        'timestamp': pd.date_range(start='2026-06-12', periods=3, freq='h'),
        'temperature_2m': [15.0, 25.0, 35.0],
        'global_radiation': [0.0, 500.0, 800.0],
        'estimated_power_kw': [0.0, 5.0, 8.0]
    })

@pytest.fixture
def mock_market_df():
    """Zwraca DataFrame o strukturze wymaganej przez tab_business."""
    return pd.DataFrame({
        'timestamp': pd.date_range(start='2026-06-12', periods=3, freq='h'),
        'price_eur_mwh': [-10.0, 50.0, 350.0]  # Zawiera cenę ujemną i bardzo wysoką
    })

@pytest.fixture
def mock_generic_bess_df():
    """Zwraca generyczny DataFrame dla tab_monitoring i tab_physics."""
    return pd.DataFrame({
        'timestamp': pd.date_range(start='2026-06-12', periods=3, freq='h'),
        'voltage_v': [1000, 1005, 998],
        'temperature_c': [22, 23, 24],
        'soc': [50, 51, 52],
        'active_power_kw': [100, -50, 0]
    })

# ==========================================
# POMOCNICZA FUNKCJA DLA MOCKOWANIA KOLUMN
# ==========================================
def mock_st_columns(spec, *args, **kwargs):
    """Zwraca odpowiednią liczbę atrap w zależności od tego, czy podano int czy listę."""
    count = spec if isinstance(spec, int) else len(spec)
    return [MagicMock() for _ in range(count)]

# ==========================================
# TESTY LOGIKI BIZNESOWEJ
# ==========================================

def test_get_top_recommendations_logic(mock_market_df, mock_weather_df):
    """Testuje, czy logika rekomendacji biznesowych poprawnie interpretuje skrajne wartości."""
    recs = _get_top_recommendations(mock_market_df, mock_weather_df)
    
    assert len(recs) <= 2, "Funkcja powinna zwracać maksymalnie 2 rekomendacje"
    assert any("GRID CHARGE OPPORTUNITY" in r for r in recs), "Nie wykryto ujemnych cen (REC_01)"
    assert any("PEAK DISCHARGE" in r for r in recs), "Nie wykryto ekstremalnych szczytów cenowych (REC_02)"

# ==========================================