
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

# Load Backend/.env
BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import the metadata and models so Alembic can detect schema changes.
from Backend.app.database.database import Base
from Backend.app.schemas import models  # noqa: F401

target_metadata = Base.metadata

# Read the application's database URL from .env.
database_url = os.getenv("DATABASE_URL")

if database_url:
    config.set_main_option(
        "sqlalchemy.url",
        database_url.replace("%", "%%")
    )


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    if not url:
        raise RuntimeError(
            "Database URL missing. Set DATABASE_URL in Backend/.env"
        )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")

    if not section["sqlalchemy.url"]:
        raise RuntimeError(
            "Database URL missing. Set DATABASE_URL in Backend/.env"
        )

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
