from logging.config import fileConfig
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add root path to sys.path for imports
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Import ALL your models here
from src.db.models.base import Base
from src.db.models.scan import ScanTarget, ScanJob, ScanResult, AccessEntry
from src.db.models.alerts import AlertConfiguration, Alert
from src.db.models.changes import PermissionChange
from src.db.models.cache import UserGroupMapping
from src.db.models.auth import ServiceAccount, AuthSession
from src.db.models.enums import ScanScheduleType, AlertType, AlertSeverity

# Import the database configuration
from config.settings import get_db_url

# this is the Alembic Config object
config = context.config

# Override the sqlalchemy.url with the one from settings
config.set_main_option('sqlalchemy.url', get_db_url())

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()