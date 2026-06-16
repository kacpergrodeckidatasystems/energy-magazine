import subprocess

import pytest


class TestAirflowSystem:
    """System tests verifying DAGs and Airflow engine correctness."""

    def run_docker_exec(self, command: list[str]) -> str:
        """Helper function to run commands inside the scheduler container."""
        base_cmd = ["docker", "compose", "exec", "-T", "airflow-scheduler"]
        result = subprocess.run(base_cmd + command, capture_output=True, text=True, check=False)
        return result.stdout + result.stderr

    def test_dags_have_no_import_errors(self):
        """Forces DAG parsing error report. Checks for SyntaxError / ImportError."""
        output = self.run_docker_exec(["airflow", "dags", "report"])

        # If the command fails at Docker level
        if "No such service" in output or "Error response" in output:
            pytest.fail(f"Error communicating with Scheduler container: {output}")

        # In Airflow report we look for error information (depending on stdout formatting version)
        # We assume that in a working system the report doesn't output "Error" or "Traceback" in the error table
        assert "Traceback" not in output, f"Found import errors in DAG files!\nOutput:\n{output}"
        assert "Error" not in output, f"Found errors in DAG report!\nOutput:\n{output}"

    def test_main_pipeline_is_registered(self):
        """Checks if the main analytical pipeline is correctly loaded in Airflow database."""
        target_dag_id = "bess_telemetry_ingestion"

        output = self.run_docker_exec(["airflow", "dags", "list"])
        assert target_dag_id in output, (
            f"DAG '{target_dag_id}' was not registered in Airflow! Wrong name or parsing error."
        )
