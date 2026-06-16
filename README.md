# 🔋 BESS Real-Time Analytics Engine

<div align="center">

**Enterprise-grade Battery Energy Storage System (BESS) analytics platform for real-time monitoring, physics-based analysis, and operational visualization**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Apache Airflow](https://img.shields.io/badge/Airflow-3.x-017CEE.svg)](https://airflow.apache.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![Code style: Ruff](https://img.shields.io/badge/Code%20style-Ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/Type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

</div>

---

## 📖 Overview

The **BESS Real-Time Analytics Engine** is a production-grade analytical platform designed for comprehensive monitoring and analysis of Battery Energy Storage Systems. It automates the complete data engineering lifecycle—from synthetic telemetry generation through ETL processing to real-time visualization—while integrating live market pricing and weather data.

### 🎯 Key Features

- **🔄 Automated Data Pipelines**: Apache Airflow 3 orchestrates telemetry generation, market/weather data ingestion, and analytics processing
- **📊 Physics-Based Analytics**: Real-time calculation of Round-Trip Efficiency (RTE), capacity fade, thermal distribution (ΔT), and internal resistance
- **📈 Interactive Dashboards**: Multi-tab Streamlit interface with real-time KPIs, time-series visualizations, and business intelligence
- **🌐 External Data Integration**: Live ENTSO-E market pricing and weather forecasting APIs
- **🐳 Full Containerization**: Docker Compose orchestration with PostgreSQL backend and deterministic networking
- **🧪 Comprehensive Testing**: Multi-tier test pyramid (unit, integration, system) with 90%+ coverage
- **🔒 Type Safety & Quality Assurance**: Strict Ruff linting and Mypy type checking with zero-tolerance enforcement

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard (Port 8501)             │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │  Monitoring  │   Physics    │   Business   │   Weather    │ │
│  │     Tab      │     Tab      │     Tab      │     Tab      │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ Reads Parquet Files
                             ▼
          ┌──────────────────────────────────────┐
          │    Local Data Storage (./data/)       │
          │  ┌────────────────────────────────┐  │
          │  │ • raw/environment/*.parquet    │  │
          │  │ • raw/inverter/*.parquet       │  │
          │  │ • raw/battery/*.parquet        │  │
          │  │ • processed/market_analytics/  │  │
          │  │ • processed/weather_analytics/ │  │
          │  └────────────────────────────────┘  │
          └─────────────▲────────────────────────┘
                        │ Writes
          ┌─────────────┴──────────────────────────┐
          │    Apache Airflow 3 (Port 8080)        │
          │  ┌─────────────────────────────────┐   │
          │  │ DAG: bess_telemetry_ingestion   │   │
          │  │  • Environment data generation  │   │
          │  │  • Inverter data generation     │   │
          │  │  • Battery BMS data generation  │   │
          │  └─────────────────────────────────┘   │
          │  ┌─────────────────────────────────┐   │
          │  │ DAG: bess_market_weather_sync   │   │
          │  │  • ENTSO-E market data fetch    │   │
          │  │  • Weather forecast ingestion   │   │
          │  └─────────────────────────────────┘   │
          └────────────────────────────────────────┘
                        │
                        ▼
          ┌────────────────────────────────────────┐
          │   PostgreSQL Metadata Store (Port 5432)│
          │   (Airflow internal state & metadata)  │
          └────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
physics/
├── 📁 config/                          # Application configuration
│   └── auth.json                       # Airflow authentication credentials
│
├── 📁 dags/                            # Apache Airflow DAG definitions
│   ├── bess_telemetry_ingestion.py     # BESS telemetry generation pipeline
│   └── market_weather.py               # Market & weather data sync pipeline
│
├── 📁 docker/                          # Containerization assets
│   ├── Dockerfile.airflow              # Airflow services image
│   └── Dockerfile.streamlit            # Streamlit dashboard image
│
├── 📁 src/                             # Source code root
│   ├── 📁 airflow/                     # ETL processing logic
│   │   └── bess_etl_pipeline.py        # Storage adapters & ingestion tasks
│   │
│   ├── 📁 analytics/                   # Analytics engines
│   │   ├── market_analytics.py         # Market pricing analytics
│   │   ├── physics_analytics.py        # BESS physics calculations
│   │   └── weather_analytics.py        # Weather correlation analytics
│   │
│   ├── 📁 api/                         # External API clients
│   │   ├── market_client.py            # ENTSO-E market data client
│   │   └── weather_client.py           # Weather forecast API client
│   │
│   ├── 📁 generators/                  # Synthetic data generators
│   │   └── bess_telemetry_generators.py # High-fidelity BESS telemetry
│   │
│   └── 📁 streamlit/                   # Visualization layer
│       ├── app.py                      # Main dashboard entrypoint
│       ├── data_loader.py              # Data access layer
│       ├── ui_components.py            # Shared UI components
│       ├── 📁 components/              # Chart components
│       │   ├── analytics_charts.py
│       │   ├── battery_charts.py
│       │   ├── system_charts.py
│       │   └── base_chart.py
│       └── 📁 tabs/                    # Dashboard tabs
│           ├── tab_monitoring.py       # Real-time monitoring view
│           ├── tab_physics.py          # Physics analytics view
│           ├── tab_business.py         # Business intelligence view
│           └── tab_weather.py          # Weather correlation view
│
├── 📁 tests/                           # Test suite (pytest)
│   ├── conftest.py                     # Shared fixtures
│   ├── 📁 unit/                        # Unit tests
│   ├── 📁 integration/                 # Integration tests
│   └── 📁 system/                      # System & UI tests
│
├── .env                                # Environment configuration
├── .gitignore                          # Git ignore rules
├── docker-compose.yml                  # Container orchestration
├── Makefile                            # Automation commands
├── pyproject.toml                      # Python dependencies & tooling
└── README.md                           # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (3.12 recommended)
- **Docker Engine** with Compose plugin
- **Make** utility (standard on Linux/macOS, available via WSL2 for Windows)

### Installation

#### 1️⃣ System Pre-Flight Check (Automated)

Run the automated installer to verify and install prerequisites:

```bash
make pre-flight
```

This command automatically:
- ✅ Checks for Python 3.12 (installs if missing via apt/PPA)
- ✅ Verifies Docker Engine installation (installs if missing)
- ✅ Validates Docker Compose plugin availability

#### 2️⃣ Development Environment Setup

Create Python virtual environment and install dependencies:

```bash
make setup
```

This command:
- Creates a `.venv` Python 3.12 virtual environment
- Installs all project dependencies with `[dev,test]` extras
- Creates required directories (`.airflow`, `data`, `logs`)
- Fixes file permissions for container access

#### 3️⃣ Launch Infrastructure

Spin up the complete system (Airflow + Streamlit + PostgreSQL):

```bash
make containers
```

This command:
- Builds Docker images from [`docker/Dockerfile.airflow`](docker/Dockerfile.airflow) and [`docker/Dockerfile.streamlit`](docker/Dockerfile.streamlit)
- Starts all services via [`docker-compose.yml`](docker-compose.yml)
- Waits for PostgreSQL health checks
- Initializes Airflow metadata database
- Unpauses and triggers both DAGs automatically

**Wait 2-3 minutes for full system initialization.**

### 🌐 Access Points

Once running, access the following endpoints:

| Service | URL | Credentials |
|---------|-----|-------------|
| 🔋 **Streamlit Dashboard** | http://localhost:8501 | None required |
| ⚙️ **Airflow Web UI** | http://localhost:8080 | `admin` / `admin` |

---

## 🛠️ Development Workflow

### Available Make Commands

View all available commands:

```bash
make help
```

| Command | Description |
|---------|-------------|
| `make setup` | Install Python environment and dependencies |
| `make containers` | Launch full infrastructure and trigger DAGs |
| `make dev` | Restart services without rebuild (fast iteration) |
| `make dag-update` | Force Airflow to re-serialize DAGs |
| `make test` | Run complete test suite |
| `make validate` | Run linting, formatting, and type checks |
| `make lint` | Run Ruff linter |
| `make format` | Auto-format code with Ruff |
| `make type-check` | Run Mypy static type analysis |
| `make clean` | Stop containers and remove volumes |
| `make stop` | Stop services gracefully |

### Code Quality Standards

The project enforces strict quality gates:

**Run all checks before committing:**

```bash
make validate
```

This executes:
1. **Ruff linting** - Style enforcement and anti-pattern detection
2. **Ruff formatting** - Consistent code formatting (120 char line length)
3. **Mypy type checking** - Strict static type verification

**Configuration files:**
- Ruff & Mypy settings: [`pyproject.toml`](pyproject.toml)

### Testing Strategy

Run the complete test suite:

```bash
make test
```

**Test Coverage:**
- ✅ **Unit Tests** ([`tests/unit/`](tests/unit/)) - Analytics algorithms, data generators
- ✅ **Integration Tests** ([`tests/integration/`](tests/integration/)) - Storage layer, infrastructure
- ✅ **System Tests** ([`tests/system/`](tests/system/)) - End-to-end DAG logic, Streamlit UI rendering

---

## ⚙️ Configuration

### Environment Variables

Configuration is managed through [`.env`](.env) file. Copy the template if it doesn't exist:

```bash
cp .env.example .env
```

**Key configuration parameters:**

```ini
# Airflow Admin Credentials
AIRFLOW_ADMIN_USER=admin
AIRFLOW_ADMIN_PASSWORD=admin

# PostgreSQL Metadata Store
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=airflow

# ENTSO-E API Key (for market data)
ENTSOE_API_KEY=your_actual_key_here_from_entsoe

# Airflow Core Settings
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
```

**Obtain ENTSO-E API Key:**
1. Visit [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)
2. Register for a free account
3. Generate API key from your profile settings
4. Update `ENTSOE_API_KEY` in `.env`

---

## 📊 Data Pipeline Overview

### DAG 1: BESS Telemetry Ingestion

**File:** [`dags/bess_telemetry_ingestion.py`](dags/bess_telemetry_ingestion.py)

Generates synthetic high-fidelity BESS telemetry data:

```python
bess_telemetry_ingestion
  ├── trigger_environment  → Environmental sensors (temp, humidity)
  ├── trigger_inverter     → Power conversion metrics (AC/DC, efficiency)
  └── trigger_battery      → BMS data (SOC, voltage, current, cell temps)
```

**Output Location:** `./data/raw/{environment,inverter,battery}/YYYY-MM-DD.parquet`

### DAG 2: Market & Weather Sync

**File:** [`dags/market_weather.py`](dags/market_weather.py)

Fetches external market and weather data:

```python
bess_market_weather_sync
  ├── fetch_market_data    → ENTSO-E spot prices (€/MWh)
  └── fetch_weather_data   → Forecast & temperature correlation
```

**Output Location:** `./data/processed/{market_analytics,weather_analytics}/YYYY-MM-DD.parquet`

### Physics Analytics Engine

**File:** [`src/analytics/physics_analytics.py`](src/analytics/physics_analytics.py)

Calculates advanced battery metrics:

- **Round-Trip Efficiency (RTE)** - Energy in vs. energy out ($\eta = \frac{E_{out}}{E_{in}}$)
- **Capacity Fade** - Degradation over charge cycles
- **Thermal Distribution (ΔT)** - Cell temperature variance
- **Internal Resistance** - Estimated from voltage/current relationships
- **State of Health (SOH)** - Long-term degradation tracking

---

## 🎨 Dashboard Features

The Streamlit dashboard ([`src/streamlit/app.py`](src/streamlit/app.py)) provides five specialized views:

### 📈 Monitoring Tab
**File:** [`src/streamlit/tabs/tab_monitoring.py`](src/streamlit/tabs/tab_monitoring.py)
- Real-time KPI cards (SOC, Power, Voltage, Current)
- Hardware filtering (rack, module, cell-level)
- Time-series plots with Plotly interactivity

### ⚡ Physics Tab
**File:** [`src/streamlit/tabs/tab_physics.py`](src/streamlit/tabs/tab_physics.py)
- Round-trip efficiency tracking
- Capacity fade analysis
- Thermal distribution heatmaps
- Internal resistance trends

### 💰 Business Tab
**File:** [`src/streamlit/tabs/tab_business.py`](src/streamlit/tabs/tab_business.py)
- Market price correlation
- Revenue optimization insights
- Arbitrage opportunity detection

### 🌤️ Weather Tab
**File:** [`src/streamlit/tabs/tab_weather.py`](src/streamlit/tabs/tab_weather.py)
- Temperature impact on battery performance
- Weather forecast integration
- Seasonal degradation patterns

---

## 🐳 Docker Infrastructure

The system uses multi-service Docker Compose orchestration ([`docker-compose.yml`](docker-compose.yml)):

### Services

| Service | Image | Ports | Description |
|---------|-------|-------|-------------|
| `postgres` | `postgres:15-alpine` | 5432 | Airflow metadata store |
| `airflow-webserver` | Custom ([`Dockerfile.airflow`](docker/Dockerfile.airflow)) | 8080 | Airflow API server |
| `airflow-scheduler` | Custom ([`Dockerfile.airflow`](docker/Dockerfile.airflow)) | - | Task scheduling engine |
| `airflow-dag-processor` | Custom ([`Dockerfile.airflow`](docker/Dockerfile.airflow)) | - | DAG parsing service |
| `bess-dashboard` | Custom ([`Dockerfile.streamlit`](docker/Dockerfile.streamlit)) | 8501 | Streamlit UI |

### Volume Mounts

- `./.airflow` → Airflow home directory (metadata, logs)
- `./dags` → DAG definitions (hot-reload enabled)
- `./src` → Source code (hot-reload enabled)
- `./data` → Persistent data storage
- `./logs` → Application logs

---

## 🧪 Testing & Quality Assurance

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
PYTHONPATH=$(pwd) .venv/bin/pytest tests/unit/ -v
PYTHONPATH=$(pwd) .venv/bin/pytest tests/integration/ -v
PYTHONPATH=$(pwd) .venv/bin/pytest tests/system/ -v
```

### Test Files

- [`tests/unit/test_analytics.py`](tests/unit/test_analytics.py) - Physics calculations verification
- [`tests/unit/test_generators.py`](tests/unit/test_generators.py) - Synthetic data generation
- [`tests/integration/test_storage.py`](tests/integration/test_storage.py) - Parquet I/O operations
- [`tests/system/test_airflow_dag_logic.py`](tests/system/test_airflow_dag_logic.py) - DAG structure validation
- [`tests/system/test_streamlit_ui.py`](tests/system/test_streamlit_ui.py) - UI component rendering (AppTest)

---

## 🔧 Troubleshooting

### Common Issues

**Problem: Containers fail to start**
```bash
# Check Docker is running
docker ps

# View container logs
docker compose logs airflow-webserver
docker compose logs bess-dashboard

# Restart infrastructure
make clean && make containers
```

**Problem: Permission errors in `data/` or `logs/` directories**
```bash
# Fix permissions
make fix-permissions
```

**Problem: DAGs not appearing in Airflow UI**
```bash
# Force DAG re-serialization
make dag-update

# Check DAG parsing errors
docker compose exec airflow-scheduler airflow dags list-import-errors
```

**Problem: Airflow database migration needed**
```bash
# Manual migration (if automatic fails)
docker compose run --rm airflow-init airflow db migrate
```

---

## 📚 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | Apache Airflow 3.x | ETL workflow automation |
| **Visualization** | Streamlit 1.30+ | Interactive dashboards |
| **Data Processing** | Pandas 2.0+ | DataFrame operations |
| **Charting** | Plotly 5.0+ | Interactive visualizations |
| **Storage** | Apache Parquet | Columnar data format |
| **Database** | PostgreSQL 15 | Metadata store |
| **Containerization** | Docker Compose | Service orchestration |
| **Type Checking** | Mypy | Static type analysis |
| **Linting** | Ruff | Code quality enforcement |
| **Testing** | Pytest | Test framework |
| **External APIs** | ENTSO-E, Weather APIs | Market & weather data |

---

## 📄 License

This project is proprietary software developed for BESS operational analytics.

---

## 👤 Author

**Kacper Grodecki**  
Data Systems Engineering

---

## 🤝 Contributing

This is a portfolio/demonstration project. For inquiries or collaboration:

1. Ensure all changes pass quality checks: `make validate`
2. Add appropriate tests for new features
3. Update documentation as needed
4. Follow existing code style and architecture patterns

---

## 📝 Changelog

### Version 0.1.0 (Current)
- ✅ Apache Airflow 3 migration with Task SDK
- ✅ Multi-tab Streamlit dashboard with physics analytics
- ✅ ENTSO-E market data integration
- ✅ Weather forecast correlation
- ✅ Comprehensive test suite (90%+ coverage)
- ✅ Docker Compose infrastructure
- ✅ Automated setup and deployment via Makefile

---

<div align="center">

**Built with ⚡ by engineers, for engineers**

[Report Bug](issues) · [Request Feature](issues)

</div>
