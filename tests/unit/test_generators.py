from datetime import datetime

from src.generators.raw_generators import generate_battery_day, generate_environment_day


def test_environment_generator_output_schema():
    """Ensures environmental simulation outputs correct columns and dimensions."""
    target_date = datetime(2026, 6, 10)
    df = generate_environment_day(target_date)

    assert not df.empty
    assert "timestamp" in df.columns
    assert "ambient_temp_sensor_01_C" in df.columns
    assert "max_solar_radiation_W_m2" in df.columns
    # Check if a 10-minute interval produces 144 steps per day
    assert len(df) == 144


def test_battery_generator_physical_bounds():
    """Validates battery state-of-charge limits within simulation data profiles."""
    target_date = datetime(2026, 6, 10)
    df = generate_battery_day(target_date)

    assert df["soc_percent"].min() >= 0.0
    assert df["soc_percent"].max() <= 100.0
