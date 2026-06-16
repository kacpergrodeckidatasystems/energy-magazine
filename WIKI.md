# 📚 BESS Analytics Platform - Project Wiki

## Table of Contents
1. [What is This Project?](#what-is-this-project)
2. [Why Does It Exist?](#why-does-it-exist)
3. [Key Concepts Explained](#key-concepts-explained)
4. [System Components](#system-components)
5. [Getting Started Guide](#getting-started-guide)
6. [Using the Platform](#using-the-platform)
7. [Understanding the Data](#understanding-the-data)
8. [Advanced Usage](#advanced-usage)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [FAQ](#faq)

---

## What is This Project?

The **BESS Real-Time Analytics Engine** is a complete software platform for monitoring and analyzing Battery Energy Storage Systems (BESS). Think of it as a "mission control center" for large-scale batteries used in power grids.

### In Simple Terms

Imagine you have a massive battery that stores electricity for a city or power grid. This platform:
- **Monitors** the battery's health in real-time (temperature, charge level, power flow)
- **Analyzes** how efficiently the battery operates
- **Tracks** degradation and predicts maintenance needs
- **Integrates** market prices to optimize when to charge/discharge
- **Visualizes** everything through interactive dashboards

### What Makes It Special?

- **Automated**: Everything runs automatically—no manual intervention needed
- **Physics-Based**: Uses real engineering formulas to calculate battery performance
- **Production-Grade**: Built using industry-standard tools (Apache Airflow, Docker)
- **Real Data Integration**: Pulls live electricity market prices and weather data
- **Comprehensive**: From data generation to visualization—everything in one place

---

## Why Does It Exist?

### The Problem

Battery energy storage systems are critical infrastructure, but monitoring them is complex:
- They generate massive amounts of telemetry data every second
- Operators need to track dozens of metrics simultaneously
- Performance degradation must be detected early to prevent failures
- Market conditions affect when batteries should charge or discharge
- Weather impacts battery performance and lifespan

### The Solution

This platform provides an end-to-end solution:
1. **Data Pipeline**: Automatically collects and processes battery telemetry
2. **Analytics Engine**: Calculates physics-based metrics (efficiency, degradation, etc.)
3. **External Integration**: Fetches market prices and weather forecasts
4. **Visualization**: Presents everything in intuitive, interactive dashboards
5. **Automation**: Airflow orchestrates the entire workflow 24/7

### Who Would Use This?

- **Power Grid Operators**: Monitor battery performance in real-time
- **Energy Asset Managers**: Track ROI and optimize charge/discharge cycles
- **Battery Engineers**: Analyze degradation patterns and thermal behavior
- **Data Engineers**: Learn about building production-grade analytics platforms

---

## Key Concepts Explained

### What is a BESS?

**BESS** = **Battery Energy Storage System**

A BESS is essentially a very large battery (often the size of shipping containers) that:
- Stores electricity when it's cheap or abundant (e.g., from solar panels)
- Releases electricity when it's expensive or needed (e.g., peak demand hours)
- Helps stabilize the power grid by balancing supply and demand

### Key Battery Metrics

#### State of Charge (SOC)
- **What**: Percentage of how full the battery is (like your phone battery: 0-100%)
- **Why it matters**: Too high or low can damage batteries; optimal range is 20-80%

#### Round-Trip Efficiency (RTE)
- **What**: How much energy you get back vs. what you put in
- **Formula**: `Efficiency = (Energy Out / Energy In) × 100%`
- **Example**: If you charge with 100 kWh and get back 85 kWh, RTE = 85%
- **Why it matters**: Higher efficiency = more profitable operation

#### Capacity Fade
- **What**: How much the battery's storage capacity decreases over time
- **Why it matters**: All batteries degrade—tracking this predicts replacement needs

#### Thermal Distribution (ΔT)
- **What**: Temperature difference across battery cells
- **Symbol**: ΔT (Delta T means "change in temperature")
- **Why it matters**: Uneven temperatures indicate cooling problems or defects

#### Internal Resistance
- **What**: How much the battery "fights" against current flow
- **Why it matters**: Higher resistance = lower efficiency and more heat generation

#### State of Health (SOH)
- **What**: Overall battery condition as a percentage (100% = brand new)
- **Why it matters**: Indicates when battery needs maintenance or replacement

### Apache Airflow Explained

**Airflow** is a workflow orchestration tool that runs tasks on a schedule.

**Think of it like a cron job system on steroids:**
- You define **DAGs** (Directed Acyclic Graphs) = sequences of tasks
- Airflow runs these tasks automatically (e.g., every hour, every day)
- It handles retries, logging, and dependencies between tasks

**In this project, Airflow:**
- Generates synthetic battery telemetry data every interval
- Fetches market prices from ENTSO-E API
- Fetches weather forecasts
- Processes and stores everything in Parquet files

### Streamlit Dashboard

**Streamlit** is a Python framework for building interactive web dashboards.

**In this project:**
- Reads the processed data files
- Calculates additional analytics in real-time
- Displays everything in multiple tabs with charts and KPIs
- Updates automatically when new data arrives

### Docker & Containerization

**Docker** packages the entire application into containers—isolated, reproducible environments.

**Benefits:**
- ✅ Works identically on any computer (no "works on my machine" issues)
- ✅ All dependencies installed automatically
- ✅ Easy to start/stop the entire system
- ✅ Services (Airflow, PostgreSQL, Streamlit) work together seamlessly

---

## System Components

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    YOU ACCESS                       │
│   📊 Streamlit Dashboard (http://localhost:8501)   │
│   ⚙️  Airflow Web UI (http://localhost:8080)       │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
    ┌─────────┐         ┌──────────┐
    │ Airflow │────────▶│PostgreSQL│
    │ Engines │         │ Database │
    └────┬────┘         └──────────┘
         │
         │ Writes Data
         ▼
    ┌────────────┐
    │ ./data/    │◀───── Streamlit reads from here
    │ (Parquet)  │
    └────────────┘
```

### Component 1: Apache Airflow (Orchestration)

**Location**: http://localhost:8080 (user: `admin`, pass: `admin`)

**Purpose**: Automates the data pipeline

**Services**:
- `airflow-webserver`: Web interface for monitoring
- `airflow-scheduler`: Runs tasks on schedule
- `airflow-dag-processor`: Parses and loads DAG definitions

**DAGs (Workflows)**:

1. **`bess_telemetry_ingestion`** - Generates synthetic BESS data
   - Runs every 15 minutes (configurable)
   - Creates three types of data:
     - `environment`: Temperature, humidity, ambient conditions
     - `inverter`: AC/DC power conversion metrics
     - `battery`: BMS data (voltage, current, SOC, cell temperatures)
   - Saves to `./data/raw/*/YYYY-MM-DD.parquet`

2. **`bess_market_weather_sync`** - Fetches external data
   - Runs hourly
   - Fetches ENTSO-E electricity market prices (€/MWh)
   - Fetches weather forecasts
   - Saves to `./data/processed/*/YYYY-MM-DD.parquet`

### Component 2: Streamlit Dashboard (Visualization)

**Location**: http://localhost:8501

**Purpose**: Interactive data visualization and analysis

**Tabs**:

1. **📈 Monitoring Tab**
   - Real-time KPIs (SOC, Power, Voltage, Current)
   - Time-series charts
   - Hardware filtering (select specific racks/modules/cells)

2. **⚡ Physics Tab**
   - Round-trip efficiency calculations
   - Capacity fade tracking
   - Thermal distribution analysis
   - Internal resistance trends

3. **💰 Business Tab**
   - Market price trends
   - Revenue optimization insights
   - Cost analysis
   - Arbitrage opportunities

4. **🌤️ Weather Tab**
   - Temperature impact on performance
   - Weather forecast visualization
   - Correlation analysis

### Component 3: PostgreSQL (Metadata Store)

**Location**: Internal (port 5432)

**Purpose**: Stores Airflow's internal state
- Task history and logs
- DAG run status
- Authentication credentials
- Not used for primary data storage (that's in Parquet files)

### Component 4: Data Storage (Local Files)

**Location**: `./data/` directory

**Structure**:
```
data/
├── raw/                        # Generated telemetry
│   ├── environment/
│   ├── inverter/
│   └── battery/
└── processed/                  # Analyzed data
    ├── market_analytics/
    └── weather_analytics/
```

**Format**: Apache Parquet (compressed columnar storage)
- Efficient for analytics
- Better compression than CSV
- Fast read performance

---

## Getting Started Guide

### Prerequisites

Before you begin, ensure you have:
- **A Linux computer** (Ubuntu 20.04+ recommended) or macOS
- **At least 8 GB RAM** (16 GB recommended)
- **10 GB free disk space**
- **Internet connection** (for Docker image downloads and API access)

### Step-by-Step Installation

#### Step 1: Clone or Download the Project

```bash
cd ~/projects
# If you have the project, cd into it
cd physics
```

#### Step 2: Verify System Requirements (Automated)

Run the pre-flight check to ensure your system is ready:

```bash
make pre-flight
```

**What this does:**
- ✅ Checks if Python 3.12 is installed (installs if missing)
- ✅ Verifies Docker Engine is running
- ✅ Ensures Docker Compose plugin is available
- ✅ Reports any issues with solutions

**Expected output:**
```
✓ Python 3.12 found
✓ Docker Engine running
✓ Docker Compose available
System ready for deployment!
```

#### Step 3: Set Up Python Environment

Create a virtual environment and install all dependencies:

```bash
make setup
```

**What this does:**
1. Creates `.venv` directory with Python 3.12
2. Installs all packages from `pyproject.toml`
3. Creates required directories (`.airflow`, `data`, `logs`)
4. Fixes file permissions for Docker access

**Expected output:**
```
[1/4] Creating virtual environment...
[2/4] Installing dependencies...
[3/4] Creating directories...
[4/4] Setting permissions...
✓ Setup complete!
```

**Time**: 2-3 minutes

#### Step 4: Configure Environment Variables

Edit the `.env` file if needed (optional):

```bash
nano .env
```

**Important settings:**
```ini
# ENTSO-E API Key (optional - for real market data)
ENTSOE_API_KEY=your_key_here

# Airflow credentials (default is fine for local use)
AIRFLOW_ADMIN_USER=admin
AIRFLOW_ADMIN_PASSWORD=admin
```

**Getting an ENTSO-E API Key** (optional):
1. Visit https://transparency.entsoe.eu/
2. Register for a free account
3. Go to "My Account Settings" → "Web API Security Token"
4. Copy the token to `.env`

**Note**: The system works without a real API key—it will generate mock data.

#### Step 5: Launch the Platform

Start all services:

```bash
make containers
```

**What this does:**
1. Builds Docker images (first time: ~5 minutes)
2. Starts PostgreSQL database
3. Initializes Airflow metadata database
4. Starts Airflow webserver, scheduler, and DAG processor
5. Starts Streamlit dashboard
6. Unpauses and triggers both DAGs

**Expected output:**
```
Building Docker images...
[+] Building 156.3s (airflow, streamlit)
Starting services...
Waiting for PostgreSQL...✓
Initializing Airflow database...✓
Starting DAGs...✓

🎉 Platform is ready!

Access points:
  📊 Dashboard: http://localhost:8501
  ⚙️  Airflow:   http://localhost:8080 (admin/admin)
```

**Time**: 
- First run: 5-7 minutes (downloads images + builds)
- Subsequent runs: 30-60 seconds

#### Step 6: Verify Everything is Running

Check service status:

```bash
docker compose ps
```

**Expected output** (all should be "healthy" or "running"):
```
NAME                    STATUS
postgres                Up (healthy)
airflow-webserver       Up (healthy)
airflow-scheduler       Up
airflow-dag-processor   Up
bess-dashboard          Up
```

### First Access

#### Open the Dashboard

Navigate to: http://localhost:8501

**What you should see:**
- Header: "🔋 BESS Real-Time Analytics Dashboard"
- Four tabs: Monitoring, Physics, Business, Weather
- Initially: "No data available" (wait 1-2 minutes for first DAG run)

#### Open Airflow Web UI

Navigate to: http://localhost:8080

**Log in with:**
- Username: `admin`
- Password: `admin`

**What you should see:**
- Dashboard with two DAGs (both should show green/running)
- `bess_telemetry_ingestion` - should show recent runs
- `bess_market_weather_sync` - should show recent runs

### Wait for Data Generation

**First data appears after ~2 minutes:**
1. Airflow triggers the DAGs
2. Tasks execute and generate data
3. Parquet files appear in `./data/`
4. Refresh the Streamlit dashboard

**Check data arrival:**
```bash
ls -lh ./data/raw/battery/
# Should show .parquet files
```

---

## Using the Platform

### Daily Operations

#### Starting the Platform (After Setup)

```bash
make containers
```

Starts all services in the background. Access the dashboard at http://localhost:8501.

#### Stopping the Platform

```bash
make stop
```

Gracefully stops all containers (data is preserved).

#### Restarting After Code Changes

```bash
make dev
```

Restarts services without rebuilding images (fast iteration during development).

### Navigating the Dashboard

#### Monitoring Tab - Real-Time Telemetry

**Purpose**: See what's happening right now

**Features**:
1. **KPI Cards** (top of page):
   - Average State of Charge (%)
   - Current Power (MW)
   - Average Voltage (V)
   - Average Current (A)

2. **Time-Series Charts**:
   - **Power Flow**: Positive = discharging, Negative = charging
   - **SOC Over Time**: Watch battery fill/drain cycles
   - **Voltage Trends**: Typical range for lithium-ion
   - **Temperature Heatmap**: Cell-level thermal distribution

3. **Hardware Filters** (sidebar):
   - Select specific racks (e.g., "Rack 1")
   - Select modules within racks
   - Select individual cells
   - View aggregated or detailed data

**How to use**:
1. Open the Monitoring tab
2. Select a time range (e.g., "Last 24 hours")
3. Use filters to drill down: All → Rack 2 → Module 3 → Cell 5
4. Hover over charts for exact values
5. Click and drag to zoom on time ranges

#### Physics Tab - Advanced Analytics

**Purpose**: Understand battery performance and degradation

**Metrics Displayed**:

1. **Round-Trip Efficiency (RTE)**:
   - Line chart showing efficiency over time
   - Should be 80-95% for healthy batteries
   - Declining trend = degradation or cooling issues

2. **Capacity Fade**:
   - Shows usable capacity as percentage of original
   - New battery = 100%, acceptable = >80%
   - Steep decline = warranty claim investigation

3. **Thermal Distribution**:
   - Heatmap of cell temperatures
   - Ideal: All cells within 5°C of each other
   - Hot spots = cooling system problems

4. **Internal Resistance**:
   - Calculated from V = IR relationships
   - Increasing resistance = aging or damage

**How to interpret**:
- **Green trends** = healthy operation
- **Yellow/orange** = watch closely
- **Red** = investigate immediately

#### Business Tab - Financial Analysis

**Purpose**: Optimize revenue from battery operations

**Features**:

1. **Market Price Chart**:
   - Real-time electricity prices (€/MWh)
   - Helps identify best charge/discharge times
   - Charge when prices are low, discharge when high

2. **Revenue Calculations**:
   - Estimated earnings based on arbitrage
   - Takes into account RTE losses

3. **Optimization Suggestions**:
   - Algorithm recommends optimal schedule
   - "Buy at 2 AM (€25/MWh), Sell at 6 PM (€85/MWh)"

**How to use**:
1. Review daily price patterns
2. Compare actual charge/discharge with optimal
3. Identify missed arbitrage opportunities

#### Weather Tab - Environmental Correlation

**Purpose**: Understand how weather affects performance

**Features**:

1. **Temperature vs. Performance**:
   - Scatter plots showing correlation
   - Batteries perform best at 15-25°C

2. **Weather Forecast**:
   - Upcoming conditions
   - Helps plan maintenance (avoid extreme heat days)

3. **Seasonal Trends**:
   - Compare summer vs. winter efficiency
   - Plan for seasonal degradation

### Using Airflow Web UI

#### Viewing DAG Status

1. Navigate to http://localhost:8080
2. Log in (`admin` / `admin`)
3. Click on DAG name to see details

**DAG View**:
- **Graph**: Visual representation of task dependencies
- **Calendar**: Historical runs (green = success, red = failure)
- **Logs**: Detailed execution logs

#### Manually Triggering a DAG

Sometimes you want data immediately:

1. Go to Airflow UI
2. Find the DAG (e.g., `bess_telemetry_ingestion`)
3. Click the "Play" button (▶️) on the right
4. Confirm "Trigger DAG"
5. Wait 30-60 seconds
6. Refresh Streamlit dashboard

#### Viewing Logs

If something fails:

1. Click on the DAG run (date in "Recent Runs")
2. Click on the failed task (will be red)
3. Click "Log" tab
4. Scroll to see error messages

**Common log locations**:
- Airflow: `./logs/` directory
- Docker: `docker compose logs airflow-scheduler`

---

## Understanding the Data

### Data Flow Diagram

```
1. [Airflow DAG Runs] 
        ↓
2. [Generates/Fetches Data]
        ↓
3. [Writes Parquet Files]
        ↓
4. [Streamlit Reads Files]
        ↓
5. [Calculates Analytics]
        ↓
6. [Displays in Dashboard]
```

### Parquet File Format

**What is Parquet?**
- Columnar storage format (optimized for analytics)
- Compressed (5-10x smaller than CSV)
- Schema-enforced (columns have defined types)

**Reading Parquet files manually**:
```bash
# Activate virtual environment
source .venv/bin/activate

# Python script to read
python3 << EOF
import pandas as pd
df = pd.read_parquet('./data/raw/battery/2026-06-16.parquet')
print(df.head())
print(df.columns)
print(df.describe())
EOF
```

### Synthetic Data Generation

**Why synthetic?**
- No real BESS connected for this demo
- Generates realistic, high-fidelity telemetry
- Models real-world behavior (charge cycles, degradation, temperature)

**Realism features**:
- ✅ Proper SOC → Voltage correlation (Nernst equation)
- ✅ Temperature rise during high current
- ✅ Capacity fade over charge cycles
- ✅ Realistic power conversion losses
- ✅ Ambient temperature variation (day/night cycles)

**Data generation logic**: [`src/generators/bess_telemetry_generators.py`](src/generators/bess_telemetry_generators.py)

### Data Schema

#### Battery Telemetry Schema
```python
{
    'timestamp': datetime,
    'rack_id': int (1-4),
    'module_id': int (1-12),
    'cell_id': int (1-24),
    'voltage': float (V),
    'current': float (A),
    'soc': float (0-100%),
    'temperature': float (°C),
    'charge_cycles': int,
    'internal_resistance': float (mΩ)
}
```

#### Inverter Data Schema
```python
{
    'timestamp': datetime,
    'inverter_id': int,
    'ac_power': float (MW),
    'dc_power': float (MW),
    'ac_voltage': float (V),
    'dc_voltage': float (V),
    'efficiency': float (0-1),
    'pf': float (power factor, -1 to 1)
}
```

#### Environment Data Schema
```python
{
    'timestamp': datetime,
    'ambient_temp': float (°C),
    'humidity': float (%),
    'hvac_status': str ('cooling'/'heating'/'idle'),
    'hvac_power': float (kW)
}
```

---

## Advanced Usage

### Customizing Data Generation Parameters

Edit [`src/generators/bess_telemetry_generators.py`](src/generators/bess_telemetry_generators.py):

```python
# Change battery configuration
NUM_RACKS = 4          # Number of battery racks
MODULES_PER_RACK = 12  # Modules in each rack
CELLS_PER_MODULE = 24  # Cells per module

# Modify generation interval
SAMPLE_RATE = "1min"   # Data granularity (1min, 5min, 15min)
```

After changes:
```bash
make dag-update  # Force Airflow to reload DAGs
```

### Changing DAG Schedules

Edit DAG files in [`dags/`](dags/):

**Telemetry DAG** ([`dags/bess_telemetry_ingestion.py`](dags/bess_telemetry_ingestion.py)):
```python
@dag(
    schedule="*/15 * * * *",  # Every 15 minutes (cron syntax)
    # Change to: "*/5 * * * *" for every 5 minutes
    # Or: "@hourly" for hourly
)
```

**Market/Weather DAG** ([`dags/market_weather.py`](dags/market_weather.py)):
```python
@dag(
    schedule="@hourly",  # Every hour
    # Change to: "@daily" for daily
)
```

### Adding Custom Analytics

Create a new file in [`src/analytics/`](src/analytics/):

```python
# src/analytics/custom_analytics.py
import pandas as pd

def calculate_custom_metric(data: pd.DataFrame) -> pd.DataFrame:
    """Your custom analysis logic"""
    data['my_metric'] = data['voltage'] * data['current']
    return data
```

Use in Streamlit ([`src/streamlit/tabs/`](src/streamlit/tabs/)):
```python
from src.analytics.custom_analytics import calculate_custom_metric

# In your tab rendering function
processed = calculate_custom_metric(raw_data)
st.line_chart(processed['my_metric'])
```

### Exporting Data

Export to CSV for external analysis:

```python
import pandas as pd

# Read Parquet
df = pd.read_parquet('./data/raw/battery/2026-06-16.parquet')

# Export to CSV
df.to_csv('./exports/battery_data.csv', index=False)
```

Or use command line:
```bash
make export-data  # If implemented in Makefile
```

### Running in Production

**For actual deployment (non-demo)**:

1. **Change default passwords**:
   ```ini
   # .env
   AIRFLOW_ADMIN_PASSWORD=strongSecurePassword123!
   POSTGRES_PASSWORD=anotherStrongPassword456!
   ```

2. **Enable authentication on Streamlit**:
   - Add OAuth provider
   - Use reverse proxy with auth (Nginx + Basic Auth)

3. **Use external database**:
   - Replace local PostgreSQL with RDS/CloudSQL
   - Update connection string in `.env`

4. **Add monitoring**:
   - Integrate Prometheus metrics
   - Set up Grafana dashboards
   - Configure alerting (PagerDuty, etc.)

5. **Scale workers**:
   ```yaml
   # docker-compose.yml
   airflow-worker:
     replicas: 3  # Scale out task execution
   ```

---

## Troubleshooting Guide

### Problem: Containers won't start

**Symptoms**:
- `docker compose ps` shows "Exited" status
- Can't access http://localhost:8501

**Solutions**:

1. **Check Docker is running**:
   ```bash
   docker ps
   # If error: "Cannot connect to Docker daemon"
   sudo systemctl start docker
   ```

2. **Check logs**:
   ```bash
   docker compose logs airflow-webserver
   docker compose logs bess-dashboard
   ```

3. **Nuclear option** (clean restart):
   ```bash
   make clean     # Stops and removes everything
   make containers # Rebuild from scratch
   ```

4. **Port conflicts** (8080/8501 already in use):
   ```bash
   # Find what's using the port
   sudo lsof -i :8080
   sudo lsof -i :8501
   
   # Kill the process or change ports in docker-compose.yml
   ```

### Problem: "No data available" in Dashboard

**Symptoms**:
- Dashboard loads but shows empty charts
- KPIs display "N/A"

**Solutions**:

1. **Wait 2-3 minutes** (first DAG run takes time)

2. **Check if DAGs are running**:
   - Go to http://localhost:8080
   - Both DAGs should be "ON" (toggle in top right)
   - Check "Recent Runs" for green checkmarks

3. **Manually trigger DAGs**:
   - Click "Play" button beside each DAG
   - Wait 30 seconds
   - Refresh Streamlit

4. **Check data files exist**:
   ```bash
   ls -lh ./data/raw/battery/
   ls -lh ./data/raw/inverter/
   ls -lh ./data/raw/environment/
   # Should see .parquet files
   ```

5. **Check file permissions**:
   ```bash
   make fix-permissions
   ```

### Problem: Permission Denied Errors

**Symptoms**:
- Logs show "Permission denied" when writing files
- Containers crash on startup

**Solutions**:

1. **Fix ownership**:
   ```bash
   sudo chown -R $USER:$USER ./data ./logs ./.airflow
   chmod -R 755 ./data ./logs ./.airflow
   ```

2. **Run permission fix**:
   ```bash
   make fix-permissions
   ```

3. **Check Docker user mapping**:
   ```bash
   # Add to docker-compose.yml under each service
   user: "${UID}:${GID}"
   ```

### Problem: Airflow DAGs Not Appearing

**Symptoms**:
- Airflow UI loads but DAGs list is empty
- "Import Errors" tab shows Python errors

**Solutions**:

1. **Check for DAG parsing errors**:
   ```bash
   docker compose exec airflow-scheduler airflow dags list-import-errors
   ```

2. **Force re-serialization**:
   ```bash
   make dag-update
   ```

3. **Validate DAG syntax**:
   ```bash
   source .venv/bin/activate
   python dags/bess_telemetry_ingestion.py
   # Should complete without errors
   ```

4. **Check Python path**:
   ```bash
   docker compose exec airflow-scheduler python -c "import sys; print(sys.path)"
   # /opt/airflow should be in the list
   ```

### Problem: Streamlit Dashboard is Slow

**Symptoms**:
- Charts take >5 seconds to load
- UI feels laggy

**Solutions**:

1. **Reduce data timeframe** (in sidebar):
   - Select "Last 6 hours" instead of "Last 7 days"

2. **Optimize data loading**:
   - Edit [`src/streamlit/data_loader.py`](src/streamlit/data_loader.py)
   - Add sampling: `df = df.sample(frac=0.1)  # Use 10% of data`

3. **Add caching**:
   ```python
   @st.cache_data(ttl=300)  # Cache for 5 minutes
   def load_data():
       return pd.read_parquet('...')
   ```

4. **Allocate more Docker resources**:
   ```bash
   # Edit ~/.docker/daemon.json
   {
     "cpus": 4,
     "memory": "8192m"
   }
   ```

### Problem: ENTSO-E API Errors

**Symptoms**:
- Market data tab shows errors
- Airflow logs mention "401 Unauthorized" or "API quota exceeded"

**Solutions**:

1. **Invalid API key**:
   - Check `.env` file: `ENTSOE_API_KEY=...`
   - Verify key at https://transparency.entsoe.eu/

2. **API quota exceeded**:
   - Free tier has limits (~400 requests/day)
   - Reduce DAG frequency: Change to `schedule="@daily"`

3. **Fallback mode**:
   - System generates mock data if API fails
   - Check logs for "Using mock data" messages

### Problem: Database Migration Errors

**Symptoms**:
- Airflow won't start
- Logs show "Database needs migration"

**Solutions**:

1. **Run migration manually**:
   ```bash
   docker compose run --rm airflow-webserver airflow db migrate
   ```

2. **Reset database** (loses history):
   ```bash
   make clean  # Removes all volumes including database
   make containers  # Reinitialize
   ```

---

## FAQ

### General Questions

**Q: Do I need a real battery to use this?**
**A**: No! The system generates synthetic but realistic telemetry data. It's designed as a demonstration platform.

**Q: Can I connect to a real battery?**
**A**: Yes, but you'd need to replace the synthetic data generators with actual BMS API clients. Modify [`src/generators/bess_telemetry_generators.py`](src/generators/bess_telemetry_generators.py) to fetch from your hardware.

**Q: How much data does this generate?**
**A**: Approximately:
- 5 MB/day of battery telemetry
- 1 MB/day of inverter data
- 100 KB/day of environment data
- 500 KB/day of market/weather data
- **Total: ~7 MB/day** (compressed Parquet)

**Q: Is this production-ready?**
**A**: It's production-grade in architecture but configured for local development. For actual deployment:
- Change default passwords
- Use external database (not local PostgreSQL)
- Add authentication and TLS
- Set up monitoring and alerting

**Q: Can I use this commercially?**
**A**: Check the license. This is primarily a portfolio/demo project.

### Technical Questions

**Q: Why Parquet instead of PostgreSQL for data?**
**A**: 
- **Performance**: Columnar format optimized for analytics
- **Storage**: 5-10x better compression than CSV
- **Simplicity**: No database schema management
- **Portability**: Easy to backup, export, share
- **Cost**: No database license or hosting costs

**Q: Can I add more DAGs?**
**A**: Yes! Create new Python files in `dags/` directory:
```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(schedule="@daily", start_date=datetime(2024, 1, 1))
def my_custom_dag():
    @task
    def my_task():
        print("Hello from custom DAG!")
    my_task()

my_custom_dag()
```

**Q: How do I backup my data?**
**A**:
```bash
# Backup data files
tar -czf backup-$(date +%Y%m%d).tar.gz ./data

# Backup database (optional)
docker compose exec postgres pg_dump -U airflow airflow > airflow-backup.sql
```

**Q: Can I run this without Docker?**
**A**: Yes, but it's complex:
1. Install PostgreSQL manually
2. Install and configure Airflow
3. Set up all environment variables
4. Run Streamlit separately
**Not recommended** unless you have specific requirements.

**Q: What Python version is required?**
**A**: Python 3.12 (required). Set in [`pyproject.toml`](pyproject.toml):
```toml
requires-python = ">=3.12,<3.13"
```

### Troubleshooting Questions

**Q: Why is Airflow showing "Scheduler not running"?**
**A**: 
```bash
# Check if scheduler container is up
docker compose ps airflow-scheduler

# Restart if needed
docker compose restart airflow-scheduler

# Check logs
docker compose logs -f airflow-scheduler
```

**Q: Dashboard shows old data—how to refresh?**
**A**: Streamlit auto-refreshes every 60 seconds, but you can:
1. Click "Rerun" in top-right corner
2. Manually trigger DAG in Airflow
3. Adjust refresh rate in [`src/streamlit/app.py`](src/streamlit/app.py)

**Q: How do I clear all data and start fresh?**
**A**:
```bash
# Stop everything and remove volumes
make clean

# Remove data files
rm -rf ./data/* ./logs/* ./.airflow/*

# Restart
make containers
```

### Performance Questions

**Q: How much RAM do I need?**
**A**: 
- **Minimum**: 8 GB (may be slow)
- **Recommended**: 16 GB
- **Optimal**: 32 GB (for large datasets)

**Q: Can I run this on a Raspberry Pi?**
**A**: Theoretically yes (ARM64 support), but:
- Very slow (especially Airflow)
- Need Pi 4 with 8 GB RAM minimum
- Build times will be long
**Not recommended**

**Q: How to speed up Docker builds?**
**A**:
```bash
# Use BuildKit
export DOCKER_BUILDKIT=1
docker compose build --parallel
```

---

## Additional Resources

### Related Documentation

- [README.md](README.md) - Quick start and technical overview
- [pyproject.toml](pyproject.toml) - Python dependencies and configuration
- [docker-compose.yml](docker-compose.yml) - Container orchestration
- [Makefile](Makefile) - Automation commands

### External Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)

### Learning More

**About Battery Storage Systems**:
- [DOE Energy Storage Handbook](https://www.energy.gov/oe/energy-storage)
- [Battery University](https://batteryuniversity.com/)

**About Data Engineering**:
- [The Data Engineering Cookbook](https://github.com/andkret/Cookbook)
- [Awesome Data Engineering](https://github.com/igorbarinov/awesome-data-engineering)

---

## Contributing

This is a portfolio project, but improvements are welcome:

1. **Report bugs**: Open an issue on the GitHub repository
2. **Suggest features**: Describe your use case
3. **Submit fixes**: Follow the existing code style (`make validate`)
4. **Improve docs**: Clarity is always appreciated

---

## Project Metadata

**Version**: 0.1.0  
**Author**: Kacper Grodecki  
**License**: Proprietary  
**Last Updated**: June 2026

---

<div align="center">

**Questions? Need Help?**

Review this wiki, check the logs, or examine the source code.  
Most common issues are covered in the [Troubleshooting Guide](#troubleshooting-guide).

**Built with ⚡ for everyone interested in energy storage analytics**

</div>
