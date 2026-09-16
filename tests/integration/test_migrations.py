from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_initial_migration_creates_only_phase_one_tables(tmp_path: Path):
    database_path = tmp_path / "migration-test.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite+pysqlite:///{database_path.as_posix()}")

    command.upgrade(config, "head")

    tables = set(
        inspect(create_engine(f"sqlite+pysqlite:///{database_path.as_posix()}")).get_table_names()
    )
    assert tables == {
        "alembic_version",
        "operations",
        "operation_attempts",
        "usage_events",
        "idempotency_records",
        "operation_results",
        "temporary_inputs",
    }
