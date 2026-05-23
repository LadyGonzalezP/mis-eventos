"""Fixtures compartidas de pytest.

- `session`: SQLite en memoria, schema completo
- `client`: TestClient con DB de test inyectada
- `make_user`: factory de usuarios con token
- `asistente_headers`, `organizador_headers`, `admin_headers`: auth con Bearer
"""

from collections.abc import Callable, Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from mis_eventos.core.security import create_access_token, hash_password
from mis_eventos.db.session import get_db
from mis_eventos.main import app
from mis_eventos.models.user import User, UserRole


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


@pytest.fixture(name="make_user")
def make_user_fixture(session: Session) -> Callable[..., tuple[User, str]]:
    """Factory para crear usuarios con su JWT listo para tests.

    Uso:
        user, token = make_user(role=UserRole.ORGANIZADOR, email="org@x.com")
    """

    counter = {"n": 0}

    def _make(
        role: UserRole = UserRole.ASISTENTE,
        email: str | None = None,
        name: str = "Test User",
        password: str = "Password123",
    ) -> tuple[User, str]:
        counter["n"] += 1
        if email is None:
            email = f"user{counter['n']}@example.com"
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_access_token(user_id=user.id, role=user.role)
        return user, token

    return _make


@pytest.fixture(name="asistente_headers")
def asistente_headers_fixture(make_user: Callable[..., tuple[User, str]]) -> dict[str, str]:
    _, token = make_user(role=UserRole.ASISTENTE)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="organizador_headers")
def organizador_headers_fixture(
    make_user: Callable[..., tuple[User, str]],
) -> dict[str, str]:
    _, token = make_user(role=UserRole.ORGANIZADOR)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="admin_headers")
def admin_headers_fixture(make_user: Callable[..., tuple[User, str]]) -> dict[str, str]:
    _, token = make_user(role=UserRole.ADMIN)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(name="organizador_with_user")
def organizador_with_user_fixture(
    make_user: Callable[..., tuple[User, str]],
) -> tuple[User, dict[str, str]]:
    """Devuelve el User + headers para casos donde necesitamos el id del organizador."""
    user, token = make_user(role=UserRole.ORGANIZADOR)
    return user, {"Authorization": f"Bearer {token}"}


# Helper para construir payloads de eventos
def _future_event_payload(name: str = "Conferencia Test") -> dict[str, Any]:
    """Payload de evento valido con fechas en el futuro."""
    return {
        "name": name,
        "description": "Descripcion del evento",
        "start_date": "2030-06-01T10:00:00",
        "end_date": "2030-06-01T18:00:00",
        "location": "Bogota",
        "capacity": 100,
    }


@pytest.fixture(name="event_payload")
def event_payload_fixture() -> Callable[..., dict[str, Any]]:
    return _future_event_payload
