# BESS Real-Time Analytics Engine

### Enterprise-grade system for Battery Energy Storage System (BESS) data processing, physics-based analytics, and real-time visualization.

---

## 📝 Project Description
The **BESS Real-Time Analytics Engine** is a comprehensive, production-grade analytical environment designed for the monitoring, physical analysis, and operational visualization of Battery Energy Storage Systems (BESS). 

The system automates the entire data engineering lifecycle: from generating synthetic high-frequency battery telemetry data, through ingestion and ETL pipelining orchestrated by **Apache Airflow 3**, to advanced physics-based analytics (including round-trip efficiency (RTE), capacity fade, thermal distribution $\Delta T$, and internal resistance estimation), concluding with a real-time visualization layer built in **Streamlit**.

### Key Architectural Pillars:
* **Full Containerization**: The entire infrastructure is spun up seamlessly via Docker Compose with deterministic networking and dependency mapping.
* **Modular & OOP Architecture**: Strict separation of concerns isolating data storage and I/O access from business logic and presentation layers, adhering to the Dependency Inversion Principle (DIP).
* **Automated Orchestration**: Airflow 3 DAG implementations leveraging automatic serialization and pipeline triggers.
* **Comprehensive Quality Assurance**: A multi-tiered testing suite (Unit, Integration, System, and headless UI testing via Streamlit `AppTest`) evaluating both mathematical telemetry calculations and application layout integrity.
* **Static Verification Gatekeeping**: Zero-tolerance code style and type safety enforcement powered by Ruff and Mypy.

---

## 📂 Project Directory Tree
The repository structure enforces clean architecture standards by physically separating orchestration definitions (`dags/`), container build files (`docker/`), source code pipelines (`src/`), and the testing pyramid (`tests/`).

```text
physics/
├── config/                  # Application configuration assets (e.g., authentication)
│   └── auth.json
├── dags/                    # Apache Airflow 3 DAG definitions
│   └── raw_to_bronze_trigger.py
├── docker/                  # Dockerfiles isolated by infrastructure component
│   ├── Dockerfile.airflow
│   └── Dockerfile.streamlit
├── src/                     # Source code package root
│   ├── __init__.py
│   ├── .airflowignore       # Directory exclusion rules for the Airflow DAG parser
│   ├── airflow/             # ETL logic executed inside the compute containers
│   │   ├── __init__.py
│   │   └── raw_to_bronze_etl.py
│   ├── generators/          # High-fidelity synthetic BESS telemetry data generators
│   │   ├── __init__.py
│   │   └── raw_generators.py
│   └── streamlit/           # Streamlit analytics dashboard (OOP UI components)
│       ├── __init__.py
│       ├── app.py           # Main presentation layer entrypoint
│       ├── data_loader.py   # Storage abstraction layer implementation
│       ├── physics_analytics.py # Analytical engine (Physical and telemetry formulas)
│       └── components/      # Domain-specific UI visualization modules
│           ├── __init__.py
│           ├── base_chart.py
│           ├── analytics_charts.py
│           ├── battery_charts.py
│           └── system_charts.py
├── tests/                   # Complete test pyramid (Pytest)
│   ├── __init__.py
│   ├── conftest.py          # Unified test fixtures and environmental overrides
│   ├── integration/         # Integration tests verifying infrastructure and storage bounds
│   │   ├── test_infrastructure.py
│   │   └── test_storage.py
│   ├── system/              # End-to-end system tests, DAG evaluations, and UI rendering
│   │   ├── test_airflow_dag_logic.py
│   │   ├── test_streamlit_ui.py
│   │   └── test_system.py
│   └── unit/                # Unit tests evaluating algorithmic physics and data generation
│       ├── test_analytics.py
│       └── test_generators.py
├── .env.example             # Environment variable template
├── .gitignore               # Multi-stage production Git ignore configuration
├── docker-compose.yml       # Container orchestration (Airflow Webserver/Scheduler, Streamlit)
├── Makefile                 # Automation interface for development and CI/CD pipelines
└── pyproject.toml           # Package management dependencies and Ruff/Mypy/Pytest 
```

## configurations

# 🛠 Installation & Local Environment Setup
Prerequisites:
Ensure your development environment has the following dependencies installed:

Python 3.12 or higher

Docker and Docker Compose

Make utility (Standard on Linux/macOS, available via WSL2 for Windows)

# Step 1: Clone and Initialize the Virtual Environment
Navigate to the project root and execute the automated build sequence to construct the .venv directory and mount all required developer packages in editable mode:
```bash
make setup
```
This target updates pip, isolates system dependencies, and installs the project with [dev] extras.

# Step 2: Run Static Code Validation
Ensure your code changes fully conform to style, structural formatting, and type-safety baselines:
```bash
make validate
```
This invokes sequential checks utilizing Ruff (linting & formatting) and Mypy (strict type-checking).

# Step 3: Run the Test Pyramid
Execute the complete local test suite to verify internal analytical calculations and catch potential regressions:
```bash
make test
```
## 🏃 Deployment & System Runtime Operations
Launching Infrastructure and the Processing Pipeline
The entire BESS ecosystem is self-contained. To spin up container assets, provision default variables, and force an initial pipeline synchronization, run:
```bash
make containers
```
Under the Hood Mechanics:

Verifies the presence of a localized .env configuration file — instantiates one from .env.example if missing.

Compiles local context Dockerfiles and boots up airflow-webserver, airflow-scheduler, and the streamlit dashboard.

Blocks and polls the Airflow web endpoint (:8080) until full health check acceptance is received.

Unpauses and dynamically triggers the primary raw ingestion DAG (bess_bronze_pure_triggers_dag).

# Accessing the Web Services:
Once running, endpoints are reachable locally:

Streamlit Analytical Dashboard: http://localhost:8501

Apache Airflow Orchestration Console: http://localhost:8080

Hot-Reloading Airflow DAGs
If modifications are introduced to DAG structures or scheduled operations, you can explicitly force database re-serialization inside the scheduler instance without restarting the runtime engine:
```bash
make dag-update
```
# Environment Teardown and Cleanup
To completely halt active containers, destroy associated persistent volumes (including generated SQLite states and raw metrics caches), and strip local build files:
```bash
make clean
```
Data architecture and analytical systems engineered by Kacper Grodecki Data Systems.