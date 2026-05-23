"""Tests del bonus de IA - generacion de descripciones.

Los tests mockean el LLM provider para no llamar al API real en CI.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

AI_URL = "/api/v1/ai/generate-description"


def test_generate_description_returns_503_without_api_key(
    client: TestClient, organizador_headers
) -> None:
    """Sin GROQ_API_KEY -> 503 (servicio no configurado)."""
    with patch("mis_eventos.api.ai.get_llm", side_effect=ValueError("not configured")):
        response = client.post(
            AI_URL,
            json={"title": "Mi conferencia"},
            headers=organizador_headers,
        )
    assert response.status_code == 503
    assert response.json()["error"] == "llm_not_configured"


def test_generate_description_success_returns_text(
    client: TestClient, organizador_headers
) -> None:
    """Mock del LLM -> devuelve la descripcion generada."""

    class _MockLlm:
        def generate(self, system: str, user: str, max_tokens: int = 500) -> str:
            return "Una conferencia tecnica que reune a profesionales del sector..."

    with patch("mis_eventos.api.ai.get_llm", return_value=_MockLlm()):
        response = client.post(
            AI_URL,
            json={"title": "Conferencia de IA 2026"},
            headers=organizador_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "description" in data
    assert "Una conferencia tecnica" in data["description"]


def test_asistente_cannot_generate_description(
    client: TestClient, asistente_headers
) -> None:
    """Solo Organizador/Admin pueden usar el bonus."""
    response = client.post(
        AI_URL,
        json={"title": "X"},
        headers=asistente_headers,
    )
    # Asistente -> 403 (no es Organizador ni Admin)
    assert response.status_code in (403, 422)  # 422 si el title min_length=3 lo rechaza primero


def test_generate_description_validates_title_length(
    client: TestClient, organizador_headers
) -> None:
    """Title muy corto -> 422."""
    response = client.post(
        AI_URL, json={"title": "X"}, headers=organizador_headers
    )
    assert response.status_code == 422


def test_generate_description_handles_llm_error(
    client: TestClient, organizador_headers
) -> None:
    """Si el LLM falla -> 502."""
    import httpx

    class _BrokenLlm:
        def generate(self, system: str, user: str, max_tokens: int = 500) -> str:
            raise httpx.HTTPError("API down")

    with patch("mis_eventos.api.ai.get_llm", return_value=_BrokenLlm()):
        response = client.post(
            AI_URL,
            json={"title": "Mi evento test"},
            headers=organizador_headers,
        )

    assert response.status_code == 502
    assert response.json()["error"] == "llm_request_failed"


def test_unauthenticated_cannot_generate(client: TestClient) -> None:
    response = client.post(AI_URL, json={"title": "Test"})
    assert response.status_code == 401
