"""Tests de autenticacion y RBAC.

Cubre los flujos de:
- Registro (exito, email duplicado, password debil, role admin rechazado)
- Login (exito, credenciales invalidas)
- Validacion de tokens
- Dependency RBAC
"""

from fastapi.testclient import TestClient

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


# ============================================
# Registro
# ============================================


def test_register_success_returns_token_and_user(client: TestClient) -> None:
    response = client.post(
        REGISTER_URL,
        json={
            "name": "Lady Test",
            "email": "lady@example.com",
            "password": "Password123",
            "role": "organizador",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "lady@example.com"
    assert data["user"]["role"] == "organizador"
    assert data["user"]["name"] == "Lady Test"
    assert "id" in data["user"]


def test_register_default_role_is_asistente(client: TestClient) -> None:
    response = client.post(
        REGISTER_URL,
        json={
            "name": "Default Role",
            "email": "default@example.com",
            "password": "Password123",
        },
    )
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "asistente"


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    payload = {
        "name": "User One",
        "email": "dup@example.com",
        "password": "Password123",
    }
    first = client.post(REGISTER_URL, json=payload)
    assert first.status_code == 201

    second = client.post(REGISTER_URL, json=payload)
    assert second.status_code == 409
    data = second.json()
    assert data["error"] == "email_already_registered"
    assert "email" in data["context"]


def test_register_short_password_returns_422(client: TestClient) -> None:
    response = client.post(
        REGISTER_URL,
        json={"name": "Short", "email": "short@example.com", "password": "abc123"},
    )
    assert response.status_code == 422


def test_register_password_without_digit_returns_422(client: TestClient) -> None:
    response = client.post(
        REGISTER_URL,
        json={"name": "NoDigit", "email": "nodigit@example.com", "password": "PasswordOnly"},
    )
    assert response.status_code == 422


def test_register_with_admin_role_returns_422(client: TestClient) -> None:
    response = client.post(
        REGISTER_URL,
        json={
            "name": "Admin Attempt",
            "email": "admin@example.com",
            "password": "Password123",
            "role": "admin",
        },
    )
    assert response.status_code == 422


def test_register_invalid_email_returns_422(client: TestClient) -> None:
    response = client.post(
        REGISTER_URL,
        json={"name": "Bad", "email": "not-an-email", "password": "Password123"},
    )
    assert response.status_code == 422


# ============================================
# Login
# ============================================


def test_login_with_valid_credentials_returns_token(client: TestClient) -> None:
    client.post(
        REGISTER_URL,
        json={
            "name": "Login Test",
            "email": "login@example.com",
            "password": "Password123",
        },
    )

    response = client.post(
        LOGIN_URL, json={"email": "login@example.com", "password": "Password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


def test_login_with_wrong_password_returns_401(client: TestClient) -> None:
    client.post(
        REGISTER_URL,
        json={
            "name": "Wrong Pass",
            "email": "wrong@example.com",
            "password": "Password123",
        },
    )

    response = client.post(
        LOGIN_URL, json={"email": "wrong@example.com", "password": "WrongPassword1"}
    )
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"


def test_login_with_nonexistent_email_returns_401(client: TestClient) -> None:
    response = client.post(
        LOGIN_URL, json={"email": "ghost@example.com", "password": "Password123"}
    )
    assert response.status_code == 401
    assert response.json()["error"] == "invalid_credentials"


# ============================================
# Token format and security
# ============================================


def test_returned_token_can_be_decoded(client: TestClient) -> None:
    """El JWT devuelto debe ser valido y contener el sub correcto."""
    from mis_eventos.core.security import decode_access_token

    response = client.post(
        REGISTER_URL,
        json={
            "name": "Token Decode",
            "email": "decode@example.com",
            "password": "Password123",
            "role": "organizador",
        },
    )
    token = response.json()["access_token"]
    payload = decode_access_token(token)
    assert payload["role"] == "organizador"
    assert "sub" in payload
    assert "exp" in payload


def test_password_is_hashed_not_stored_plain(client: TestClient, session) -> None:
    """El password jamas se guarda en plano."""
    from sqlmodel import select

    from mis_eventos.models.user import User

    client.post(
        REGISTER_URL,
        json={
            "name": "Hash Test",
            "email": "hash@example.com",
            "password": "PlainPassword123",
        },
    )

    user = session.exec(select(User).where(User.email == "hash@example.com")).first()
    assert user is not None
    assert user.password_hash != "PlainPassword123"
    assert user.password_hash.startswith("$2b$")  # bcrypt prefix
