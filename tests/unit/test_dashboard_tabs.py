from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.streamlit.tabs.tab_business import _get_top_recommendations

# Imports of your tab functions

# ==========================================
# FIXTURES (Test data preparation)
# ==========================================

@pytest.fixture
def mock_weather_df():
    """Returns DataFrame with structure required by tab_weather and tab_business."""
    return pd.DataFrame({
        'timestamp': pd.date_range(start='2026-06-12', periods=3, freq='h'),
        'temperature_2m': [15.0, 25.0, 35.0],
        'global_radiation': [0.0, 500.0, 800.0],
        'estimated_power_kw': [0.0, 5.0, 8.0]
    })

@pytest.fixture
def mock_market_df():
    """Returns DataFrame with structure required by tab_business."""
    return pd.DataFrame({
        'timestamp': pd.date_range(start='2026-06-12', periods=3, freq='h'),
        'price_eur_mwh': [-10.0, 50.0, 350.0]  # Contains negative price and very high price
    })

@pytest.fixture
def mock_generic_bess_df():
    """Returns generic DataFrame for tab_monitoring and tab_physics."""
    return pd.DataFrame({
        'timestamp': pd.date_range(start='2026-06-12', periods=3, freq='h'),
        'voltage_v': [1000, 1005, 998],
        'temperature_c': [22, 23, 24],
        'soc': [50, 51, 52],
        'active_power_kw': [100, -50, 0]
    })

# ==========================================
# HELPER FUNCTION FOR MOCKING COLUMNS
# ==========================================
def mock_st_columns(spec, *args, **kwargs):
    """Returns appropriate number of mocks depending on whether int or list was provided."""
    count = spec if isinstance(spec, int) else len(spec)
    return [MagicMock() for _ in range(count)]

# ==========================================
# BUSINESS LOGIC TESTS
# ==========================================

def test_get_top_recommendations_logic(mock_market_df, mock_weather_df):
    """Tests if business recommendation logic correctly interprets extreme values."""
    recs = _get_top_recommendations(mock_market_df, mock_weather_df)

    assert len(recs) <= 2, "Function should return maximum 2 recommendations"
    assert any("GRID CHARGE OPPORTUNITY" in r for r in recs), "Negative prices not detected (REC_01)"
    assert any("PEAK DISCHARGE" in r for r in recs), "Extreme price peaks not detected (REC_02)"

# ==========================================
