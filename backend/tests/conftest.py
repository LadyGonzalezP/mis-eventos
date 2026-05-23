"""Fixtures compartidas de pytest.

- `client`: TestClient con DB en memoria (SQLite) que se recrea por test
- `session`: Sesion de SQLModel sobre la DB en memoria

Asi los tests son rapidos, aislados y NO requieren Postgres corriendo.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from mis_eventos.db.session import get_db
from mis_eventos.main import app


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """SQLite en memoria - aislado, sin red, super rapido."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """TestClient con la DB de test inyectada."""

    def get_db_override() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db] = get_db_override
    yield TestClient(app)
    app.dependency_overrides.clear()
