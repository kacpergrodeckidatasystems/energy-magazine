import subprocess

import pytest


class TestAirflowSystem:
    """Testy systemowe weryfikujące poprawność DAG-ów i silnika Airflow."""

    def run_docker_exec(self, command: list[str]) -> str:
        """Pomocnicza funkcja do uruchamiania komend wewnątrz kontenera schedulera."""
        base_cmd = ["docker", "compose", "exec", "-T", "airflow-scheduler"]
        result = subprocess.run(base_cmd + command, capture_output=True, text=True, check=False)
        return result.stdout + result.stderr

    def test_dags_have_no_import_errors(self):
        """Wymusza raport błędów parsowania DAG-ów. Sprawdza, czy nie ma SyntaxError / ImportError."""
        output = self.run_docker_exec(["airflow", "dags", "report"])

        # Jeśli polecenie się nie powiedzie na poziomie Dockera
        if "No such service" in output or "Error response" in output:
            pytest.fail(f"Błąd komunikacji z kontenerem Schedulera: {output}")

        # W raporcie Airflow szukamy informacji o błędach (w zależności od wersji formatowania stdout)
        # Zakładamy, że w sprawnym systemie raport nie wypluwa słowa "Error" lub "Traceback" w tabeli błędów
        assert "Traceback" not in output, f"Znaleziono błędy importu w plikach DAG!\nOutput:\n{output}"
        assert "Error" not in output, f"Znaleziono błędy w raporcie DAG!\nOutput:\n{output}"

    def test_main_pipeline_is_registered(self):
        """Sprawdza, czy główny potok analityczny jest poprawnie załadowany w bazie Airflow."""
        target_dag_id = "bess_bronze_pure_triggers_dag"

        output = self.run_docker_exec(["airflow", "dags", "list"])
        assert target_dag_id in output, (
            f"DAG '{target_dag_id}' nie został zarejestrowany w Airflow! Zła nazwa lub błąd parsowania."
        )
