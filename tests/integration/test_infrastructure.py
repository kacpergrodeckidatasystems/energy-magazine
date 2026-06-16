import os

import pytest
import requests
from requests.exceptions import ConnectionError

import docker


class TestInfrastructure:
    """Integration tests checking environment and Docker containers correctness."""

    def test_environment_variables_loaded(self):
        """Checks if key variables from .env file are available in the host environment."""
        required_vars = ["AIRFLOW_ADMIN_USER", "AIRFLOW_ADMIN_PASSWORD", "POSTGRES_USER", "POSTGRES_PASSWORD"]
        # NOTE: This test assumes you export .env before running tests,
        # which will be done automatically in Makefile.
        for var in required_vars:
            assert os.getenv(var) is not None, f"Missing critical environment variable: {var}"

    def test_docker_containers_are_running_and_healthy(self):
        """Checks if all required Docker services have 'running' status."""
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
            assert is_running, f"Critical container is not running: {service}"

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
        """Checks if the Streamlit analytics dashboard started correctly."""
        url = "http://localhost:8501/_stcore/health"
        try:
            response = requests.get(url, timeout=5)
            assert response.status_code == 200, "Streamlit Dashboard is not responding (HTTP 200)"
        except ConnectionError:
            pytest.fail("Cannot connect to Dashboard (port 8501).")
