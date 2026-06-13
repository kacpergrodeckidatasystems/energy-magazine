"""
Streamlit UI Components Module

This module provides reusable UI components for the BESS dashboard application.
It implements the DRY (Don't Repeat Yourself) principle by centralizing common
UI patterns used across different dashboard tabs.

Main Features:
    - Sidebar configuration (date selection)
    - Hardware filtering (rack and module selection)
    - KPI metric display panels
    - Consistent styling and formatting

Components:
    - render_sidebar_config(): Date selection interface
    - render_hardware_filters(): Battery asset filtering
    - render_kpi_panel(): Key performance indicator display

Design Benefits:
    - Reusability: Components used across multiple tabs
    - Consistency: Uniform UI patterns throughout app
    - Maintainability: Single source of truth for UI logic
    - Testability: Isolated components for unit testing

UI Philosophy:
    - User-friendly: Clear labels and helpful messages
    - Defensive: Graceful handling of empty data
    - Informative: Warning messages guide user actions
    - Efficient: Caching and optimization where possible

Dependencies:
    - streamlit: UI framework
    - pandas: Data manipulation
    - datetime: Date formatting

Author: BESS Operations Team
Version: 1.0.0
"""

from datetime import datetime

import pandas as pd

import streamlit as st


def render_sidebar_config(data_loader) -> str:
    """
    Render date selection interface in sidebar and return selected date.

    This component creates the main configuration panel in the Streamlit sidebar,
    allowing users to select which date's data to analyze. It discovers available
    dates dynamically from the data loader and presents them in a user-friendly
    format.

    Component Features:
        - Automatic date discovery from data files
        - User-friendly date formatting (YYYY-MM-DD display)
        - Warning message when no data available
        - Application stop on missing data (prevents errors)

    Workflow:
        1. Display sidebar header with icon
        2. Query available dates from data loader
        3. Check if dates exist
        4. If no dates: Show warning and stop execution
        5. If dates exist: Display selectbox with formatted dates
        6. Return selected date in YYYYMMDD format

    Args:
        data_loader (BESSDataLoader): Data loader instance for discovering
                                     available dates in the file system.

    Returns:
        str: Selected date in YYYYMMDD format (e.g., "20240613").
             This format matches the filename convention used in data storage.

    Raises:
        st.stop(): Application execution halts if no data available.
                  Prevents downstream errors from missing data.

    UI Elements:
        - Header: "📅 Configuration"
        - Selectbox: Date picker with formatted display
        - Warning: Shown when data directory is empty

    Date Formatting:
        Storage format: YYYYMMDD (e.g., "20240613")
        Display format: YYYY-MM-DD (e.g., "2024-06-13")
        User sees: 2024-06-13
        Function returns: 20240613

    Example:
        >>> from data_loader import BESSDataLoader
        >>> loader = BESSDataLoader()
        >>>
        >>> # Render sidebar (within Streamlit app)
        >>> selected_date = render_sidebar_config(loader)
        >>> print(selected_date)
        '20240613'
        >>>
        >>> # Now use selected_date to load data
        >>> df_env, df_inv, df_bat = loader.load_daily_data(selected_date)

    User Experience:
        No data scenario:
        - User sees: "No data found in directory! Please trigger the Airflow DAG first."
        - Application stops gracefully
        - Clear guidance on next steps

        Data available scenario:
        - User sees dropdown with dates: 2024-06-13, 2024-06-14, etc.
        - Can select any available date
        - Most recent date typically at bottom

    Integration:
        Called early in app.py to establish which data to load.
        Selected date propagates to all downstream components.

    Note:
        - Uses st.stop() to halt execution on missing data
        - format_func in selectbox converts display format
        - Sidebar placement keeps config persistent across tabs
    """
    # Display sidebar header with calendar icon
    st.sidebar.header("📅 Configuration")

    # Query data loader for available dates
    # available_dates: List of strings in YYYYMMDD format
    # Example: ['20240610', '20240611', '20240612', '20240613']
    available_dates = data_loader.get_available_dates()

    # Check if any data exists
    if not available_dates:
        # No data found: Show warning and stop execution
        st.sidebar.warning("No data found in directory! Please trigger the Airflow DAG first.")

        # Stop application to prevent errors from missing data
        # This is a graceful failure mode that guides user to solution
        st.stop()

    # Display date selectbox with formatted dates
    # selected_date_str: The internally stored date format (YYYYMMDD)
    selected_date_str = st.sidebar.selectbox(
        "Select analysis date:",  # Label for selectbox
        available_dates,  # List of YYYYMMDD strings
        format_func=lambda x: datetime.strptime(x, "%Y%m%d").strftime("%Y-%m-%d"),
        # format_func: Converts YYYYMMDD → YYYY-MM-DD for display
        # User sees: "2024-06-13" but value remains "20240613"
    )

    return selected_date_str


def render_hardware_filters(df_bat: pd.DataFrame) -> pd.DataFrame:
    """
    Render hardware filtering interface and return filtered battery DataFrame.

    This component creates multi-select filters for battery racks and modules,
    allowing users to focus analysis on specific hardware assets. It enhances
    module identification by creating composite IDs that combine rack and module
    information for clearer visualization.

    Component Features:
        - Hierarchical filtering (rack → module)
        - Multi-select capability (analyze multiple units)
        - Enhanced module ID generation (rack + module)
        - Default selection of all available hardware
        - Dynamic updates based on rack selection

    Filtering Hierarchy:
        1. Select racks (e.g., rack_01, rack_02)
        2. Available modules update based on rack selection
        3. Select specific modules from available set
        4. Return filtered dataset

    Enhanced Module ID:
        Original: rack_id="rack_01", battery_module_id="battery_module_01"
        Enhanced: global_module_id="Rack 01 | bat1"

        Benefits:
        - Clearer in charts and legends
        - Combines rack and module information
        - More compact than separate fields
        - Human-readable format

    Args:
        df_bat (pd.DataFrame): Battery telemetry DataFrame containing:
                              - rack_id: Rack identifier (e.g., "rack_01")
                              - battery_module_id: Module ID (e.g., "battery_module_01")
                              - Other telemetry columns (voltage, current, etc.)

    Returns:
        pd.DataFrame: Filtered battery DataFrame containing only selected modules.
                     Includes new column:
                     - global_module_id: Enhanced identifier (e.g., "Rack 01 | bat1")

                     DataFrame preserves all original columns plus global_module_id.
                     Empty DataFrame if no modules selected (with global_module_id column).

    UI Elements:
        Sidebar Section:
        - Header: "🎛️ Asset Filtering"
        - Multiselect 1: "🗄️ Rack Unit:" - Select racks
        - Multiselect 2: "🔋 Battery Module:" - Select modules

    Example:
        >>> # With 2 racks and 5 modules each
        >>> df_bat = pd.DataFrame({
        ...     'rack_id': ['rack_01', 'rack_01', 'rack_02', 'rack_02'],
        ...     'battery_module_id': ['battery_module_01', 'battery_module_02',
        ...                           'battery_module_01', 'battery_module_02'],
        ...     'voltage': [3.6, 3.5, 3.7, 3.6]
        ... })
        >>>
        >>> # User selects: rack_01, rack_02 (all racks)
        >>> # User selects: "Rack 01 | bat1", "Rack 02 | bat1" (first module of each)
        >>> df_filtered = render_hardware_filters(df_bat)
        >>>
        >>> print(df_filtered['global_module_id'].unique())
        ['Rack 01 | bat1', 'Rack 02 | bat1']
        >>>
        >>> len(df_filtered)
        2  # Only selected modules

    User Interaction Flow:
        1. User opens sidebar
        2. Sees all available racks (default: all selected)
        3. Can deselect racks to narrow scope
        4. Module list updates to show only modules from selected racks
        5. Can further filter to specific modules
        6. Visualization updates in real-time

    Edge Cases:
        - No racks selected: Module list is empty
        - No modules selected: Returns empty DataFrame with schema
        - Single rack system: Hierarchy still works
        - Module ID format variations: Handles gracefully

    Performance:
        - Filtering: O(n) where n = number of battery records
        - String operations: Efficient pandas vectorized operations
        - UI updates: Near-instant for typical datasets

    Integration:
        Called in app.py after data loading and before analytics.
        Filtered DataFrame used throughout all visualization tabs.

    Note:
        - Uses .copy() to avoid SettingWithCopyWarning
        - Default selection prevents empty initial state
        - Sorted lists provide consistent ordering
        - global_module_id used in charts and tables
    """
    # Add visual separator and header
    st.sidebar.markdown("---")
    st.sidebar.header("🎛️ Asset Filtering")

    # Get all unique racks and sort for consistent ordering
    # all_racks: List of unique rack identifiers (e.g., ['rack_01', 'rack_02'])
    all_racks = sorted(df_bat["rack_id"].unique())

    # Rack selection multiselect
    # selected_racks: List of rack IDs chosen by user
    # default=all_racks: All racks selected initially
    selected_racks = st.sidebar.multiselect(
        "🗄️ Rack Unit:",  # Label with icon
        options=all_racks,  # All available racks
        default=all_racks,  # Default: select all
    )

    # Filter battery data by selected racks
    # df_bat_rack_filtered: Contains only data from selected racks
    # .copy(): Avoid pandas SettingWithCopyWarning when adding columns
    df_bat_rack_filtered = df_bat[df_bat["rack_id"].isin(selected_racks)].copy()

    # Generate enhanced module IDs
    if not df_bat_rack_filtered.empty:
        # Create composite global_module_id
        # Example transformation:
        # rack_id="rack_01" + battery_module_id="battery_module_01"
        # → global_module_id="Rack 01 | bat1"

        df_bat_rack_filtered["global_module_id"] = (
            # Convert rack_id: "rack_01" → "Rack 01"
            df_bat_rack_filtered["rack_id"].str.replace("_", " ").str.title()
            + " | "  # Separator
            # Convert module_id: "battery_module_01" → "bat1"
            + df_bat_rack_filtered["battery_module_id"].str.replace("battery_module_", "bat")
        )

        # Get available modules after rack filtering
        # available_modules: Sorted list of enhanced module IDs
        available_modules = sorted(df_bat_rack_filtered["global_module_id"].unique())
    else:
        # No racks selected: Empty module list and empty column
        df_bat_rack_filtered["global_module_id"] = []
        available_modules = []

    # Module selection multiselect
    # selected_modules: List of enhanced module IDs chosen by user
    # default=available_modules: All available modules selected initially
    selected_modules = st.sidebar.multiselect(
        "🔋 Battery Module:",  # Label with icon
        options=available_modules,  # Modules from selected racks
        default=available_modules,  # Default: select all
    )

    # Return final filtered DataFrame
    # Contains only rows matching selected modules
    return df_bat_rack_filtered[df_bat_rack_filtered["global_module_id"].isin(selected_modules)]


def render_kpi_panel(df_env: pd.DataFrame, metrics: dict) -> None:
    """
    Render key performance indicator (KPI) panel with system metrics.

    This component displays a prominent metrics panel showing the most important
    operational indicators for the BESS. It uses Streamlit's column layout to
    create a professional dashboard appearance with clear, at-a-glance metrics.

    Component Features:
        - Four-column layout for balanced display
        - Icon-enhanced subheader
        - Formatted metric values with units
        - Horizontal separator for visual structure

    Metrics Displayed:
        1. Max Ambient Temperature: Peak environmental temperature
        2. Round-Trip Efficiency (RTE): Energy recovery ratio
        3. Total Charged: Energy absorbed from grid/solar
        4. Total Discharged: Energy delivered to grid

    Args:
        df_env (pd.DataFrame): Environment telemetry DataFrame containing:
                              - ambient_temp_sensor_01_C: Temperature readings (°C)
                              - Other environmental columns

        metrics (dict): Pre-computed physics metrics dictionary with keys:
                       - rte_percent (float): Round-trip efficiency percentage
                       - total_charged_MWh (float): Total energy charged in MWh
                       - total_discharged_MWh (float): Total energy discharged in MWh

    Returns:
        None: Renders UI components directly to Streamlit app.
             No return value (display function).

    UI Layout:
        ┌─────────────────────────────────────────────────────────────┐
        │        📊 Key Performance Indicators                        │
        ├──────────────┬──────────────┬──────────────┬───────────────┤
        │ Max Ambient  │    RTE       │ Charged      │ Discharged    │
        │   26.8 °C    │   89.5 %     │  12.50 MWh   │  11.19 MWh    │
        └──────────────┴──────────────┴──────────────┴───────────────┘

    Metric Formatting:
        - Temperature: 1 decimal place (e.g., 26.8 °C)
        - RTE: 1 decimal place (e.g., 89.5 %)
        - Energy: 2 decimal places (e.g., 12.50 MWh)

    Example:
        >>> import pandas as pd
        >>> from analytics.physics_analytics import BESSPhysicsAnalytics
        >>>
        >>> # Load data
        >>> df_env = pd.DataFrame({'ambient_temp_sensor_01_C': [25.0, 26.8, 25.5]})
        >>> df_inv = pd.DataFrame({'active_power_output_MW': [1.0, -0.8, 1.2]})
        >>>
        >>> # Calculate metrics
        >>> engine = BESSPhysicsAnalytics(sampling_interval_minutes=10)
        >>> metrics = engine.calculate_energy_and_rte(df_inv)
        >>>
        >>> # Render KPI panel (within Streamlit app)
        >>> render_kpi_panel(df_env, metrics)
        >>> # Displays: Max Ambient: 26.8 °C, RTE: 92.3%, etc.

    Data Requirements:
        df_env must contain:
        - ambient_temp_sensor_01_C: Valid numeric temperature values

        metrics must contain:
        - rte_percent: Float, typically 80-95 for healthy BESS
        - total_charged_MWh: Float, typically 0-100 MWh/day
        - total_discharged_MWh: Float, slightly less than charged

    Visual Design:
        - Equal-width columns for balanced layout
        - Consistent formatting across metrics
        - Clear labels with units
        - Professional dashboard appearance
        - Separator for visual structure

    Interpretation Guide:
        Max Ambient Temp:
        - Typical: 20-35 °C
        - High (>35°C): Check cooling system
        - Low (<15°C): Consider heating requirements

        RTE (Round-Trip Efficiency):
        - Excellent: >92%
        - Good: 88-92%
        - Fair: 85-88%
        - Poor: <85% (investigate losses)

        Energy Balance:
        - Charged ≈ Discharged: Balanced operation
        - Charged > Discharged: SOC increasing (normal)
        - Charged < Discharged: SOC decreasing (check charging)

    Integration:
        Called in app.py after data loading and metric calculation.
        Appears at top of dashboard before tab navigation.

    Note:
        - Uses st.metric() for formatted display
        - Columns create responsive layout
        - Markdown separator improves visual hierarchy
        - No error handling needed (metrics pre-validated)
    """
    # Display subheader with icon
    st.subheader("📊 Key Performance Indicators")

    # Create four equal-width columns
    # col1, col2, col3, col4: Column objects for metric placement
    col1, col2, col3, col4 = st.columns(4)

    # Column 1: Maximum ambient temperature from sensor 01
    # max(): Find peak temperature across all time periods
    # {:.1f}: Format to 1 decimal place
    col1.metric(
        "Max Ambient Temp",  # Metric label
        f"{df_env['ambient_temp_sensor_01_C'].max():.1f} °C",  # Formatted value with unit
    )

    # Column 2: Round-Trip Efficiency
    # Indicates how much energy can be recovered
    # {:.1f}: Format to 1 decimal place
    col2.metric(
        "Round-Trip Efficiency (RTE)",  # Metric label
        f"{metrics['rte_percent']:.1f} %",  # Formatted percentage
    )

    # Column 3: Total energy charged
    # Energy absorbed from grid or solar
    # {:.2f}: Format to 2 decimal places for precision
    col3.metric(
        "Total Charged (PV)",  # Metric label
        f"{metrics['total_charged_MWh']:.2f} MWh",  # Formatted energy value
    )

    # Column 4: Total energy discharged
    # Energy delivered back to grid
    # {:.2f}: Format to 2 decimal places
    col4.metric(
        "Total Discharged (Grid)",  # Metric label
        f"{metrics['total_discharged_MWh']:.2f} MWh",  # Formatted energy value
    )

    # Add horizontal separator for visual structure
    # Markdown "---" creates a thin horizontal line
    st.markdown("---")
