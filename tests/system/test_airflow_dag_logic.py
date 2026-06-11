import pytest
from airflow.models import DagBag


@pytest.fixture
def dagbag():
    return DagBag(dag_folder="dags/", include_examples=False)


def test_dag_structure(dagbag):
    """Checks if the main pipeline has the correct task flow."""
    dag = dagbag.get_dag("bess__pure_triggers_dag")
    assert dag is not None

    tasks = dag.task_dict.keys()

    assert "trigger_environment" in tasks
    assert "trigger_inverter" in tasks
    assert "trigger_batteries" in tasks
