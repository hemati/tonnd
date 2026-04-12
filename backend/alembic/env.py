import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from src.models.db_models import Base
import src.models.api_models  # noqa: F401 — register APIToken + AuditLog with Base
import src.models.fitbit_models  # noqa: F401 — register typed Fitbit tables

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Sync driver for migrations (Alembic doesn't support asyncpg directly)
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://healthcoach:healthcoach@localhost:5432/healthcoach",
).replace("+asyncpg", "+psycopg2").replace("?ssl=disable", "")


def run_migrations_offline() -> None:
    context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
