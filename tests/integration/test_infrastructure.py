import os

import pytest
import requests
from requests.exceptions import ConnectionError

import docker


class TestInfrastructure:
    """Testy integracyjne sprawdzające poprawność środowiska i kontenerów Dockera."""

    def test_environment_variables_loaded(self):
        """Sprawdza, czy kluczowe zmienne z pliku .env są dostępne w środowisku hosta."""
        required_vars = ["AIRFLOW_ADMIN_USER", "AIRFLOW_ADMIN_PASSWORD", "POSTGRES_USER", "POSTGRES_PASSWORD"]
        # UWAGA: Ten test zakłada, że eksportujesz .env przed uruchomieniem testów,
        # co zrobimy automatycznie w Makefile.
        for var in required_vars:
            assert os.getenv(var) is not None, f"Brak krytycznej zmiennej środowiskowej: {var}"

    def test_docker_containers_are_running_and_healthy(self):
        """Sprawdza, czy wszystkie wymagane usługi Dockera mają status 'running'."""
        client = docker.from_env()
        running_containers = [c.name for c in client.containers.list()]

        required_services = [
            "postgres",
            "airflow-webserver",
            "airflow-scheduler",
            "airflow-dag-processor",
            "bess-dashboard",
        ]

        for service in required_services:
            is_running = any(service in name for name in running_containers)
            assert is_running, f"Krytyczny kontener nie działa: {service}"

    def test_airflow_webserver_health(self):
        """Checks if the Airflow UI is responsive."""
        # Change /health to /ui/ or /home/ which triggers the app check
        url = "http://localhost:8080/ui/"
        try:
            response = requests.get(url, timeout=10)
            # We accept 200 (Success)
            assert response.status_code == 200, f"Airflow UI returned error: {response.status_code}"
        except ConnectionError:
            pytest.fail("Cannot connect to Airflow Webserver on port 8080.")

    def test_streamlit_dashboard_health(self):
        """Sprawdza, czy analityczny dashboard Streamlit wstał poprawnie."""
        url = "http://localhost:8501/_stcore/health"
        try:
            response = requests.get(url, timeout=5)
            assert response.status_code == 200, "Streamlit Dashboard nie odpowiada (HTTP 200)"
        except ConnectionError:
            pytest.fail("Nie można połączyć się z Dashboardem (port 8501).")
