from sqlalchemy import text
from db.database import engine, init_db
from db.models import Model, Task, BenchmarkRecord


def test_init_db_creates_tables():
    """init_db should create all tables in the database."""
    init_db()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = {row[0] for row in result}
    assert "models" in tables
    assert "tasks" in tables
    assert "benchmark_records" in tables
