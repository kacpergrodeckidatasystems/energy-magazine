import os
import tempfile

import pytest

if "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN" in os.environ:
    del os.environ["AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"]

fd, db_path = tempfile.mkstemp(suffix=".db")
os.close(fd)

os.environ["AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"] = f"sqlite:////{db_path}"
os.environ["AIRFLOW__CORE__LOAD_EXAMPLES"] = "False"
os.environ["AIRFLOW__CORE__UNIT_TEST_MODE"] = "True"

from airflow.utils import db


@pytest.fixture(scope="session", autouse=True)
def init_airflow_db():
    """Initializes a clean, isolated file-based SQLite database for tests."""
    db.initdb()
    yield
    # Sprzątanie po zakończeniu sesji testowej
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass
