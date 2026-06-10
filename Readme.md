# BESS Real-Time Diagnostic & Analytical Platform

An enterprise-grade Battery Energy Storage System (BESS) telemetry simulation, orchestration, and analytical dashboard. This platform mirrors real-world Industrial Internet of Things (IIoT) architectures, streaming synthetic multi-rack Battery Management System (BMS) and Power Conversion System (PCS) telemetry into a structured bronze data lake layer, followed by advanced physical degradation analytics.

---

## 🏗️ System Architecture & Data Flow

The platform is designed around decoupling infrastructure from business logic, ensuring strict adherence to **SOLID principles** and **Object-Oriented Programming (OOP)**.

1. **Telemetry Simulation Engine (`src/generators/`)**: A deterministic physical engine modeling diurnal solar cycles, Gaussian charging/discharging prongs, thermal lag inertia ($I^2R$ Joule heating), and discrete cell anomalies (Voltage Sags & local HVAC failures).
2. **Orchestration Layer (`dags/`, `src/airflow/`)**: Built for **Airflow 3 TaskFlow SDK**. Ingests whole-day telemetry bursts and utilizes an abstracted storage interface driver (`DataStorage`) to dump optimized binary Apache Parquet tables.
3. **Analytical SCADA Interface (`src/streamlit/`)**: A high-performance dashboard that dynamically caches bronze data, provides granular multi-hardware filtering, and processes complex physical analytics vectors (RTE integrations, Delta-T dispersion, and $R_{int}$ hysteresis loops).

---

## 🔬 Injected Physical Anomalies

The data engine injects real-world operational issues to validate the diagnostic capabilities of the SCADA layer:
* **Rack 01 - Module 02 (Voltage Sag / Internal Resistance Anomaly)**: Simulates electrochemical cell degradation (SoH drop). During high discharge current, it triggers massive voltage drops, creating skewed linear trends in $U$ vs $I$ scatter matrices.
* **Rack 02 - Module 04 (Thermal Runaway Risk)**: Simulates localized HVAC strefa ventilation blocking or coolant leaks. Thermal profile spikes exponentially tied directly to the square of the rack operating current ($I^2R$).

---

## 🛠️ Tech Stack & Code Quality Framework

* **Core Runtime**: Python 3.13
* **Orchestration**: Apache Airflow 3.2.0 (Next-Gen TaskFlow Bundle Architecture)
* **Data Layer**: Pandas 2.0.0, PyArrow (Parquet engine)
* **Visualization**: Streamlit, Plotly Express & Graph Objects
* **Code Quality & CI**: Ruff (Linter & Formatter), Mypy (Strict Static Typing), GitHub Actions

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have Python 3.13+, Docker, and GNU Make installed on your host system.

### 2. Environment Initialization
Build the local virtual environment and install the package along with its rigorous development dependencies (`ruff`, `mypy`, type stubs) via the provided Makefile:

```bash
make setup
```
## 3. Spin Up Infrastructure
```bash
make containers
```
## 4. Populate the Data Lake
```bash
make dag-update
```
## 5. Development & CI Verification Pipeline
```bash
make validate
```