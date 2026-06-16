# ============================================================================
# Makefile for BESS Analytics Platform
# ============================================================================
# Automation for:
#   - Pre-flight system checks (Docker, Python 3.11 verification & installation)
#   - Development environment setup (Python virtual environment)
#   - Docker infrastructure orchestration (Airflow + Streamlit)
#   - Code quality checks (linting, formatting, type checking)
#   - Testing and validation workflows
#
# Quick Start:
#   make setup       - Pre-flight check, create venv (Python 3.12), install deps
#   make containers  - Launch full infrastructure and trigger DAGs
#   make test        - Run test suite
#   make help        - Display all available commands
# ============================================================================

# --- ENVIRONMENT VARIABLES ---
VENV_NAME    := .venv
PYTHON       := $(VENV_NAME)/bin/python
PIP          := $(VENV_NAME)/bin/pip
RUFF         := $(VENV_NAME)/bin/ruff
MYPY         := $(VENV_NAME)/bin/mypy

.PHONY: help pre-flight setup containers dag-update lint format type-check validate clean test fix-permissions dev stop

# ============================================================================
# HELP & DOCUMENTATION
# ============================================================================

help: ## Display this help screen with all available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# SYSTEM PRE-FLIGHT CHECKS (Docker & Python 3.12 enforcement)
# ============================================================================

pre-flight: ## Check and install prerequisites (Python 3.12 and Docker Engine)
	@echo "🔍 Executing pre-flight system checks..."
	
	# 1. Check/Install Python 3.12
	@command -v python3.12 >/dev/null 2>&1 || { \
		echo "⚠️ Python 3.12 not found. Installing via apt (Ubuntu/Debian)..." >&2; \
		sudo apt-get update && \
		sudo apt-get install -y software-properties-common && \
		sudo add-apt-repository -y ppa:deadsnakes/ppa && \
		sudo apt-get update && \
		sudo apt-get install -y python3.12 python3.12-venv python3.12-dev python3.12-distutils; \
	}
	
	# 2. Check/Install Docker Engine
	@command -v docker >/dev/null 2>&1 || { \
		echo "⚠️ Docker not found. Installing Docker Engine..." >&2; \
		sudo apt-get update && \
		sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release && \
		curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
		echo "deb [arch=$$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $$(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null && \
		sudo apt-get update && \
		sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin && \
		sudo usermod -aG docker $$USER && \
		echo "👉 Please restart your terminal/WSL session to apply docker group permissions." ; \
	}
	
	# 3. Check Docker Compose Plugin
	@docker compose version >/dev/null 2>&1 || { \
		echo "❌ Docker Compose plugin is missing, please ensure installation completed." >&2; \
		exit 1; \
	}
	@echo "✅ All prerequisites satisfied (Python 3.12 & Docker available)."

# ============================================================================
# DEVELOPMENT ENVIRONMENT SETUP
# ============================================================================

$(VENV_NAME):  # Create Python 3.12 virtual environment
	python3.12 -m venv $(VENV_NAME)

# ============================================================================
# INFRASTRUCTURE & ORCHESTRATION
# ============================================================================

containers: ## Spin up Docker infrastructure (Airflow + Streamlit) and trigger DAGs
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo "🚀 Launching infrastructure..."
	@docker compose up --build -d
	
	@echo "⏳ Czekam na pełną gotowość bazy danych PostgreSQL..."
	@until docker compose exec -T postgres pg_isready -U postgres > /dev/null; do sleep 2; done
	
	@echo "🔍 Sprawdzanie realnego stanu struktur tabel w bazie..."
	@# Sprawdzamy, czy w bazie danych istnieje tabela 'slot_pool' (podstawowa tabela Airflow)
	@if docker compose exec -T postgres psql -U postgres -d airflow -c "SELECT to_regclass('public.slot_pool');" 2>/dev/null | grep -q "slot_pool"; then \
		echo "✅ Tabele Airflow istnieją. Pomijam pełną migrację (Skip db migrate)."; \
	else \
		echo "🗄️ Baza danych jest pusta. Uruchamiam 'airflow db migrate'..."; \
		docker compose run --rm -T airflow-init airflow db migrate; \
	fi
	
	@echo "⏳ Waiting for Airflow Webserver to be ready..."
	@until curl -s -I http://localhost:8080/ | grep -q "HTTP/"; do sleep 3; done	
	@echo "🔍 Checking for DAG registration..."
	@for dag in bess_telemetry_ingestion bess_market_weather_sync; do \
		echo "Waiting for $$dag to be registered..."; \
		until docker compose exec -T airflow-scheduler airflow dags list | grep -q "$$dag"; do \
			sleep 5; \
		done; \
		echo "✅ $$dag found. Unpausing..."; \
		docker compose exec -T airflow-scheduler airflow dags unpause $$dag; \
		echo "🚀 Triggering $$dag..."; \
		docker compose exec -T airflow-scheduler airflow dags trigger $$dag; \
	done
	
	@echo "✨ Pipeline fully triggered. Dashboard available at http://localhost:8501"
	@echo "✨ Airflow fully triggered, available at http://localhost:8080"

dag-update: ## Force Airflow 3 to re-serialize DAGs (use after modifying DAG files)
	docker compose exec -T airflow-scheduler airflow dags reserialize

stop: ## Stop all services and remove volumes (clean shutdown)
	@docker compose down -v

dev: ## Restart services without rebuilding (fast iteration during development)
	@echo "🔄 Restarting services without rebuilding..."
	@docker compose restart bess-dashboard airflow-scheduler airflow-dag-processor

# ============================================================================
# CODE QUALITY & VALIDATION
# ============================================================================

lint: ## Run Ruff linter to check code style and potential errors
	@$(RUFF) check src/ dags/

format: ## Auto-format code with Ruff formatter (modifies files in place)
	@$(RUFF) format src/ dags/

type-check: ## Run Mypy static type checker to verify type annotations
	@$(MYPY) src/ dags/

validate: lint format type-check  ## Run all code quality checks

# ============================================================================
# TESTING & VALIDATION
# ============================================================================

test: ## Run complete test suite (unit, integration, system tests)
	@echo "Running test suite..."
	@bash -c "set -a; source .env; set +a; PYTHONPATH=$(shell pwd) $(VENV_NAME)/bin/pytest tests/ -v"

# ============================================================================
# CLEANUP & MAINTENANCE
# ============================================================================

clean: ## Clean workspace (remove Docker containers, volumes, and virtual environment)
	@docker compose down -v
	@rm -rf $(VENV_NAME) config/

setup: pre-flight | $(VENV_NAME)  ## Run pre-flight, set up Python 3.12 venv, dirs and start infrastructure
	@$(PIP) install --upgrade pip
	@$(PIP) install -e .[dev,test]
	@touch $(VENV_NAME)/bin/activate
	@if [ ! -d ".airflow" ]; then \
		echo "📁 Katalog '.airflow' nie istnieje. Tworzę..."; \
		mkdir -p .airflow; \
	else \
		echo "✅ Katalog '.airflow' już istnieje. Pomijam."; \
	fi
	@if [ ! -d "data" ]; then \
		echo "Creating 'data' directory..."; \
		mkdir -p data; \
	else \
		echo "Directory 'data' already exists, skipping creation."; \
	fi
	@if [ ! -d "logs" ]; then \
		echo "Creating 'logs' directory..."; \
		mkdir -p logs; \
	fi
	@echo "🛡️  Ustawianie poprawnych uprawnień deweloperskich..."
	@$(MAKE) fix-permissions

fix-permissions: ## Fix ownership and permissions for runtime directories (.airflow, data, logs)
	@echo "⚙️  Fixing permissions for folder 'data'..."
	@sudo mkdir -p data
	@sudo chown -R $(USER):$(USER) data
	@sudo chmod -R 777 data
	@echo "⚙️  Fixing permissions for folder 'logs'..."
	@sudo mkdir -p logs
	@sudo chmod -R 777 logs
	@echo "⚙️  Fixing permissions for folder '.airflow'..."
	@sudo mkdir -p .airflow
	@sudo chmod -R 777 .airflow/
	@echo "✅ Uprawnienia dla katalogów roboczych zostały naprawione!"