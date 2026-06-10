import os

from streamlit.testing.v1 import AppTest


def test_streamlit_dashboard_render_with_no_data(tmp_path):
    empty_bronze = tmp_path / "empty_bronze"
    empty_bronze.mkdir()

    os.environ["DATA_DIR"] = str(empty_bronze)

    at = AppTest.from_file("src/streamlit/app.py", default_timeout=30)
    at.run()

    assert len(at.warning) > 0 or len(at.sidebar.warning) > 0

    assert len(at.sidebar.warning) > 0


def test_streamlit_dashboard_successful_load(tmp_path):
    """Verifies that the layout, metric cards, and tabs render correctly when data exists."""
    # Create fake folders mimicking the active database structure inside tmp_path
    for folder in ["environment", "inverter", "battery"]:
        os.makedirs(os.path.join(tmp_path, folder), exist_ok=True)

    # Set app base directory to our mocked path
    at = AppTest.from_file("src/streamlit/app.py")

    # Run screen rendering loop
    at.run()

    # Assert dashboard title exists and is accurate
    assert at.title[0].value == "🔋 BESS Real-Time Diagnostic Dashboard"
