"""Tests del endpoint /health.

Verifica que el sistema reporta correctamente su estado de salud:
- Siempre responde 200 (el endpoint vive si responde)
- Estructura JSON con status, db, version
- db = "ok" si la conexion funciona

Este es el primer endpoint del sistema y prueba que toda la base esta lista:
- FastAPI configurado
- DB session injectable
- Exception handlers no rompen
"""

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    """El endpoint /health debe responder con 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_has_required_fields(client: TestClient) -> None:
    """La respuesta debe incluir status, db y version."""
    response = client.get("/health")
    data = response.json()
    assert "status" in data
    assert "db" in data
    assert "version" in data


def test_health_db_is_ok_with_working_session(client: TestClient) -> None:
    """Con una sesion DB funcionando, db debe ser 'ok'."""
    response = client.get("/health")
    data = response.json()
    assert data["db"] == "ok"


def test_health_status_is_ok_when_db_works(client: TestClient) -> None:
    """status debe ser 'ok' cuando la DB esta operativa."""
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_returns_version(client: TestClient) -> None:
    """version debe coincidir con la configurada en Settings."""
    response = client.get("/health")
    data = response.json()
    assert data["version"] == "0.1.0"
