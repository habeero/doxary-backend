from logging.config import fileConfig

from alembic import context
from app.core.config.settings import Settings
from app.core.database.metadata import Base
from app.idempotency.record import IdempotencyRecord  # noqa: F401
from app.operations.infrastructure.attempt_record import OperationAttemptRecord  # noqa: F401
from app.operations.infrastructure.operation_record import OperationRecord  # noqa: F401
from app.operations.infrastructure.operation_result_record import (
    OperationResultRecord,  # noqa: F401
)
from app.usage.infrastructure.usage_event_record import UsageEventRecord  # noqa: F401
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
settings = Settings.load()
if "database_url" in settings.model_fields_set:
    config.set_main_option("sqlalchemy.url", settings.resolved_database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
