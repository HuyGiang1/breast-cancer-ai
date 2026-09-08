import pytest
from app.core.database import db, DB_PATH


@pytest.fixture(autouse=True)
def isolate_test_database(tmp_path):
    """
    Prevents tests from polluting the persistent backend/data/app.db.
    Each test session/function executes against an isolated SQLite database.
    """
    test_db_path = tmp_path / "test_app.db"
    original_path = db.db_path
    db.db_path = test_db_path
    db.init()
    yield test_db_path
    db.db_path = original_path
