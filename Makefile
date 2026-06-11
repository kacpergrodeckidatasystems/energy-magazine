# --- ENVIRONMENT VARIABLES ---
VENV_NAME := .venv
PYTHON    := $(VENV_NAME)/bin/python
PIP       := $(VENV_NAME)/bin/pip
RUFF      := $(VENV_NAME)/bin/ruff
MYPY      := $(VENV_NAME)/bin/mypy

.PHONY: help setup containers dag-update lint format type-check validate clean

help: ## Display this help screen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: | $(VENV_NAME)
	@$(PIP) install --upgrade pip
	@$(PIP) install -e .[dev]
	@touch $(VENV_NAME)/bin/activate
	@mkdir -p data
	@echo "Give programe permissions to create/manage files in 'data' folder..."
	@$(MAKE) fix-permissions

$(VENV_NAME):
	python3 -m venv $(VENV_NAME)

# --- INFRASTRUCTURE & AUTOMATION ---
containers: ## Spin up infrastructure and trigger pipeline
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo "Launching infrastructure..."
	@docker compose up --build -d
	@echo "Waiting for Airflow Webserver to be ready..."
	@until curl -s http://localhost:8080/ui/ > /dev/null; do sleep 5; done
	@echo "Airflow is up. Triggering pipeline..."
	@docker compose exec -T airflow-scheduler airflow dags unpause bess_bronze_pure_triggers_dag
	@docker compose exec -T airflow-scheduler airflow dags trigger bess_bronze_pure_triggers_dag
	@echo "Pipeline triggered. Dashboard available at http://localhost:8501"

dag-update: ## Force Airflow 3 to re-serialize
	docker compose exec -T airflow-scheduler airflow dags reserialize

# --- QUALITY ---
lint:
	@$(RUFF) check src/ dags/

format:
	@$(RUFF) format src/ dags/

type-check:
	@$(MYPY) src/ dags/

validate: lint format type-check

clean: ## Clean workspace
	@docker compose down -v
	@rm -rf $(VENV_NAME) config/

stop: ## stop workspace
	@docker compose down -v

# --- TESTING & VALIDATION ---
test:
	@echo "Running test suite..."
	@bash -c "set -a; source .env; set +a; PYTHONPATH=$(shell pwd) $(VENV_NAME)/bin/pytest tests/ -v"

fix-permissions:
	@echo "Fixing permissions for folder 'data'..."
	@sudo chown -R $(USER):$(USER) data
	@chmod -R 775 data