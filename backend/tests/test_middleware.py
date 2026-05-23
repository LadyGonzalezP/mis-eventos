"""Tests de middlewares: request_id + security headers + CORS."""

from fastapi.testclient import TestClient


def test_response_has_x_request_id_header(client: TestClient) -> None:
    response = client.get("/health")
    assert "x-request-id" in {k.lower() for k in response.headers}


def test_response_echoes_request_id_when_sent_in_header(client: TestClient) -> None:
    custom_id = "11111111-2222-3333-4444-555555555555"
    response = client.get("/health", headers={"X-Request-Id": custom_id})
    assert response.headers["x-request-id"] == custom_id


def test_security_headers_present(client: TestClient) -> None:
    response = client.get("/health")
    headers = {k.lower(): v for k, v in response.headers.items()}
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert "strict-transport-security" in headers
    assert "referrer-policy" in headers


def test_cors_preflight_allowed_for_configured_origin(client: TestClient) -> None:
    """OPTIONS request desde un origen whitelisteado debe ser permitido."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    # CORS middleware responde 200 a OPTIONS si el origen es valido
    assert response.status_code in (200, 204)
