# ============================================================================
# Makefile for BESS Analytics Platform
# ============================================================================
# This Makefile provides automation for:
#   - Development environment setup (Python virtual environment)
#   - Docker infrastructure orchestration (Airflow + Streamlit)
#   - Code quality checks (linting, formatting, type checking)
#   - Testing and validation workflows
#
# Quick Start:
#   make setup       - Create virtual environment and install dependencies
#   make containers  - Launch full infrastructure and trigger DAGs
#   make test        - Run test suite
#   make help        - Display all available commands
# ============================================================================

# --- ENVIRONMENT VARIABLES ---
# Python virtual environment configuration for local development
VENV_NAME := .venv
PYTHON    := $(VENV_NAME)/bin/python
PIP       := $(VENV_NAME)/bin/pip
RUFF      := $(VENV_NAME)/bin/ruff
MYPY      := $(VENV_NAME)/bin/mypy

# Declare all targets as phony (not actual files) to ensure they always run
.PHONY: help setup containers dag-update lint format type-check validate clean test fix-permissions dev stop

# ============================================================================
# HELP & DOCUMENTATION
# ============================================================================

help: ## Display this help screen with all available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# DEVELOPMENT ENVIRONMENT SETUP
# ============================================================================

setup: | $(VENV_NAME)  ## Set up Python virtual environment and install dependencies
	@$(PIP) install --upgrade pip              # Upgrade pip to latest version
	@$(PIP) install -e .[dev]                  # Install project in editable mode with dev dependencies
	@touch $(VENV_NAME)/bin/activate          # Touch activate script to update timestamp
	@if [ ! -d "data" ]; then \
		echo "Creating 'data' directory and fixing permissions..."; \
		mkdir -p data; \
		$(MAKE) fix-permissions; \
	else \
		echo "Directory 'data' already exists, skipping creation and permission fix."; \
	fi

$(VENV_NAME):  # Create Python virtual environment if it doesn't exist
	python3 -m venv $(VENV_NAME)

# ============================================================================
# INFRASTRUCTURE & ORCHESTRATION
# ============================================================================

containers: ## Spin up Docker infrastructure (Airflow + Streamlit) and trigger DAGs
	@if [ ! -f .env ]; then cp .env.example .env; fi  # Create .env from example if missing
	@echo "🚀 Launching infrastructure..."
	@docker compose up --build -d                      # Build and start all services in detached mode
	
	@echo "⏳ Waiting for Airflow Webserver to be ready..."
	@until curl -s http://localhost:8080/ui/ > /dev/null; do sleep 5; done  # Poll until UI is accessible
	
	@echo "🔍 Checking for DAG registration..."
	# Wait for DAGs to be parsed and serialized by dag-processor, then unpause and trigger them
	@for dag in bess_pure_triggers_dag bess_market_weather_sync; do \
		echo "Waiting for $$dag to be registered..."; \
		until docker compose exec -T airflow-scheduler airflow dags list | grep -q "$$dag"; do \
			sleep 5; \
		done; \
		echo "✅ $$dag found. Unpausing..."; \
		docker compose exec -T airflow-scheduler airflow dags unpause $$dag;   # Enable DAG scheduling
		echo "🚀 Triggering $$dag..."; \
		docker compose exec -T airflow-scheduler airflow dags trigger $$dag;   # Manually trigger first run
	done
	
	@echo "✨ Pipeline fully triggered. Dashboard available at http://localhost:8501"

dag-update: ## Force Airflow 3 to re-serialize DAGs (use after modifying DAG files)
	docker compose exec -T airflow-scheduler airflow dags reserialize  # Reparse and update serialized DAGs

stop: ## Stop all services and remove volumes (clean shutdown)
	@docker compose down -v

dev: ## Restart services without rebuilding (fast iteration during development)
	@echo "🔄 Restarting services without rebuilding..."
	@docker compose restart bess-dashboard airflow-scheduler airflow-dag-processor

# ============================================================================
# CODE QUALITY & VALIDATION
# ============================================================================

lint: ## Run Ruff linter to check code style and potential errors
	@$(RUFF) check src/ dags/  # Scan source code and DAGs for issues

format: ## Auto-format code with Ruff formatter (modifies files in place)
	@$(RUFF) format src/ dags/  # Reformat code to follow style guidelines

type-check: ## Run Mypy static type checker to verify type annotations
	@$(MYPY) src/ dags/  # Check type consistency across codebase

validate: lint format type-check  ## Run all code quality checks (lint + format + type-check)

# ============================================================================
# TESTING & VALIDATION
# ============================================================================

test: ## Run complete test suite (unit, integration, system tests)
	@echo "Running test suite..."
	@bash -c "set -a; source .env; set +a; PYTHONPATH=$(shell pwd) $(VENV_NAME)/bin/pytest tests/ -v"
	# Load environment variables, set PYTHONPATH, and execute pytest with verbose output

# ============================================================================
# CLEANUP & MAINTENANCE
# ============================================================================

clean: ## Clean workspace (remove Docker containers, volumes, and virtual environment)
	@docker compose down -v      # Stop containers and remove volumes
	@rm -rf $(VENV_NAME) config/ # Remove virtual environment and config directory

fix-permissions: ## Fix ownership and permissions for the data directory (requires sudo)
	@echo "Fixing permissions for folder 'data'..."
	@sudo chown -R $(USER):$(USER) data  # Change owner to current user
	@chmod -R 775 data                    # Set read/write/execute for user and group