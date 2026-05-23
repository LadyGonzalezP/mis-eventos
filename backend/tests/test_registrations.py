"""Tests de inscripciones a eventos."""

from typing import Any

from fastapi.testclient import TestClient

EVENTS_URL = "/api/v1/events"
ME_URL = "/api/v1/me/registrations"


def _create_published_event(
    client: TestClient,
    headers: dict[str, str],
    event_payload,
    name: str = "Conf",
    capacity: int = 100,
) -> dict[str, Any]:
    payload = event_payload(name=name)
    payload["capacity"] = capacity
    created = client.post(EVENTS_URL, json=payload, headers=headers).json()
    client.post(f"{EVENTS_URL}/{created['id']}/publish", headers=headers)
    return created


# ============================================
# Registro a evento
# ============================================


def test_user_can_register_to_published_event(
    client: TestClient, organizador_headers, asistente_headers, event_payload
) -> None:
    event = _create_published_event(client, organizador_headers, event_payload)
    response = client.post(
        f"{EVENTS_URL}/{event['id']}/register", headers=asistente_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == event["id"]


def test_register_to_draft_event_fails(
    client: TestClient, organizador_headers, asistente_headers, event_payload
) -> None:
    """No se puede inscribir a un evento en borrador."""
    draft = client.post(
        EVENTS_URL, json=event_payload(name="Draft"), headers=organizador_headers
    ).json()
    response = client.post(
        f"{EVENTS_URL}/{draft['id']}/register", headers=asistente_headers
    )
    assert response.status_code == 400
    assert response.json()["error"] == "event_not_open_for_registration"


def test_register_twice_returns_409(
    client: TestClient, organizador_headers, asistente_headers, event_payload
) -> None:
    event = _create_published_event(client, organizador_headers, event_payload)
    client.post(f"{EVENTS_URL}/{event['id']}/register", headers=asistente_headers)
    response = client.post(
        f"{EVENTS_URL}/{event['id']}/register", headers=asistente_headers
    )
    assert response.status_code == 409
    assert response.json()["error"] == "already_registered"


def test_register_when_full_returns_409(
    client: TestClient,
    organizador_headers,
    asistente_headers,
    event_payload,
    make_user,
) -> None:
    """Capacity 1 -> el segundo asistente no puede inscribirse."""
    event = _create_published_event(client, organizador_headers, event_payload, capacity=1)

    # Primer asistente OK
    r1 = client.post(f"{EVENTS_URL}/{event['id']}/register", headers=asistente_headers)
    assert r1.status_code == 201

    # Segundo asistente -> sin cupo
    _, other_token = make_user(role="asistente", email="other@example.com")
    r2 = client.post(
        f"{EVENTS_URL}/{event['id']}/register",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert r2.status_code == 409
    assert r2.json()["error"] == "event_full"


def test_register_unauthenticated_returns_401(
    client: TestClient, organizador_headers, event_payload
) -> None:
    event = _create_published_event(client, organizador_headers, event_payload)
    response = client.post(f"{EVENTS_URL}/{event['id']}/register")
    assert response.status_code == 401


# ============================================
# Cancelar inscripcion
# ============================================


def test_cancel_own_registration_works(
    client: TestClient, organizador_headers, asistente_headers, event_payload
) -> None:
    event = _create_published_event(client, organizador_headers, event_payload)
    client.post(f"{EVENTS_URL}/{event['id']}/register", headers=asistente_headers)

    response = client.delete(
        f"{EVENTS_URL}/{event['id']}/register", headers=asistente_headers
    )
    assert response.status_code == 204

    # Verificar que ya no esta inscrito
    me = client.get(ME_URL, headers=asistente_headers)
    assert me.json() == []


def test_cancel_when_not_registered_returns_404(
    client: TestClient, organizador_headers, asistente_headers, event_payload
) -> None:
    event = _create_published_event(client, organizador_headers, event_payload)
    response = client.delete(
        f"{EVENTS_URL}/{event['id']}/register", headers=asistente_headers
    )
    assert response.status_code == 404


# ============================================
# Mis inscripciones
# ============================================


def test_my_registrations_returns_user_events(
    client: TestClient, organizador_headers, asistente_headers, event_payload
) -> None:
    event1 = _create_published_event(client, organizador_headers, event_payload, name="Evento A")
    event2 = _create_published_event(client, organizador_headers, event_payload, name="Evento B")

    client.post(f"{EVENTS_URL}/{event1['id']}/register", headers=asistente_headers)
    client.post(f"{EVENTS_URL}/{event2['id']}/register", headers=asistente_headers)

    response = client.get(ME_URL, headers=asistente_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {item["event_name"] for item in data}
    assert names == {"Evento A", "Evento B"}


def test_my_registrations_empty_for_new_user(
    client: TestClient, asistente_headers
) -> None:
    response = client.get(ME_URL, headers=asistente_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_my_registrations_requires_auth(client: TestClient) -> None:
    response = client.get(ME_URL)
    assert response.status_code == 401
