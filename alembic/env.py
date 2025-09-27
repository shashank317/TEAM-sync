from logging.config import fileConfig
import os
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

if not os.getenv("RENDER"):
    from dotenv import load_dotenv
    load_dotenv()

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import Base
from models import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def _normalize_db_url(url: str) -> str:
    if not url:
        return url
    try:
        # Upgrade deprecated scheme
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and "+psycopg2" not in url.split("//", 1)[1]:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        parsed = urlparse(url)
        host = parsed.hostname or ""
        q = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if any(s in host for s in ("render.com", "neon.tech")) and "sslmode" not in q:
            q["sslmode"] = "require"
            parsed = parsed._replace(query=urlencode(q))
            url = urlunparse(parsed)
        return url
    except Exception:
        return url


db_url = os.getenv("DATABASE_URL")
if not db_url and os.getenv("USE_SQLITE", "0") == "1":
    db_url = os.getenv("SQLITE_PATH", "sqlite:///./teamsync.db")

config.set_main_option('sqlalchemy.url', _normalize_db_url(db_url))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
