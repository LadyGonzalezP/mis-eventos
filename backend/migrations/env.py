"""Alembic environment - configura las migraciones contra SQLModel.

Lee DATABASE_URL del entorno (via mis_eventos.core.config.settings) en vez del
sqlalchemy.url del .ini para mantener un solo lugar de configuracion.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel  # noqa: F401 - necesario para que se registren los models

# Importar todos los models aqui para que Alembic los detecte
# (se iran agregando en cada slice)
# from mis_eventos.models import user, event, session, speaker, registration  # noqa: F401
from mis_eventos.core.config import settings

config = context.config

# Inyectar la URL de DB desde nuestra config (no del .ini)
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Migraciones en modo offline - genera SQL sin conexion real a DB."""
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
    """Migraciones en modo online - aplica directo sobre la DB real."""
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
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
