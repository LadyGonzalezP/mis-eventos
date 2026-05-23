"""Gestion de sesiones de base de datos.

Expone `engine` (instancia singleton) y `get_db` (dependency de FastAPI para
inyectar sesiones en endpoints).
"""

from collections.abc import Generator

from sqlmodel import Session, create_engine

from mis_eventos.core.config import settings

engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)


def get_db() -> Generator[Session, None, None]:
    """Dependency de FastAPI - abre una sesion por request y la cierra al final."""
    with Session(engine) as session:
        yield session
