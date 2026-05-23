"""Tests de endpoints de eventos - CRUD + state machine + permisos."""

from typing import Any

from fastapi.testclient import TestClient

EVENTS_URL = "/api/v1/events"


# ============================================
# CREATE
# ============================================


def test_organizador_can_create_event(
    client: TestClient,
    organizador_headers: dict[str, str],
    event_payload,
) -> None:
    response = client.post(EVENTS_URL, json=event_payload(), headers=organizador_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Conferencia Test"
    assert data["status"] == "borrador"
    assert data["capacity"] == 100


def test_admin_can_create_event(
    client: TestClient,
    admin_headers: dict[str, str],
    event_payload,
) -> None:
    response = client.post(EVENTS_URL, json=event_payload(), headers=admin_headers)
    assert response.status_code == 201


def test_asistente_cannot_create_event(
    client: TestClient,
    asistente_headers: dict[str, str],
    event_payload,
) -> None:
    response = client.post(EVENTS_URL, json=event_payload(), headers=asistente_headers)
    assert response.status_code == 403
    assert response.json()["error"] == "forbidden"


def test_unauthenticated_cannot_create_event(
    client: TestClient, event_payload
) -> None:
    response = client.post(EVENTS_URL, json=event_payload())
    assert response.status_code == 401


def test_create_event_with_end_before_start_returns_422(
    client: TestClient, organizador_headers: dict[str, str], event_payload
) -> None:
    payload = event_payload()
    payload["end_date"] = "2030-05-01T10:00:00"  # Antes que start_date
    payload["start_date"] = "2030-06-01T10:00:00"
    response = client.post(EVENTS_URL, json=payload, headers=organizador_headers)
    assert response.status_code == 422


def test_create_event_with_zero_capacity_returns_422(
    client: TestClient, organizador_headers: dict[str, str], event_payload
) -> None:
    payload = event_payload()
    payload["capacity"] = 0
    response = client.post(EVENTS_URL, json=payload, headers=organizador_headers)
    assert response.status_code == 422


# ============================================
# LIST
# ============================================


def _create_and_publish(
    client: TestClient,
    headers: dict[str, str],
    name: str,
    payload_factory,
) -> dict[str, Any]:
    payload = payload_factory(name=name)
    create_resp = client.post(EVENTS_URL, json=payload, headers=headers)
    assert create_resp.status_code == 201
    event = create_resp.json()
    publish_resp = client.post(
        f"{EVENTS_URL}/{event['id']}/publish", headers=headers
    )
    assert publish_resp.status_code == 200
    return publish_resp.json()


def test_list_only_shows_published_by_default(
    client: TestClient, organizador_headers: dict[str, str], event_payload
) -> None:
    """Sin filtro de status, solo se ven los publicados."""
    # Crear uno borrador
    client.post(EVENTS_URL, json=event_payload(name="Draft"), headers=organizador_headers)
    # Crear y publicar otro
    _create_and_publish(client, organizador_headers, "Published", event_payload)

    response = client.get(EVENTS_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Published"


def test_list_with_search_filters_by_partial_name(
    client: TestClient, organizador_headers: dict[str, str], event_payload
) -> None:
    _create_and_publish(client, organizador_headers, "Python Conf 2026", event_payload)
    _create_and_publish(client, organizador_headers, "React Workshop", event_payload)

    response = client.get(f"{EVENTS_URL}?q=python")
    data = response.json()
    assert data["total"] == 1
    assert "Python" in data["items"][0]["name"]


def test_list_pagination_works(
    client: TestClient, organizador_headers: dict[str, str], event_payload
) -> None:
    for i in range(15):
        _create_and_publish(client, organizador_headers, f"Event {i:02d}", event_payload)

    page1 = client.get(f"{EVENTS_URL}?page=1&limit=10").json()
    page2 = client.get(f"{EVENTS_URL}?page=2&limit=10").json()
    assert page1["total"] == 15
    assert len(page1["items"]) == 10
    assert len(page2["items"]) == 5


# ============================================
# DETAIL
# ============================================


def test_get_event_returns_detail(
    client: TestClient, organizador_headers: dict[str, str], event_payload
) -> None:
    created = client.post(EVENTS_URL, json=event_payload(), headers=organizador_headers).json()
    response = client.get(f"{EVENTS_URL}/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_nonexistent_event_returns_404(client: TestClient) -> None:
    response = client.get(f"{EVENTS_URL}/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


# ============================================
# UPDATE
# ============================================


def test_organizador_can_update_own_event(
    client: TestClient, organizador_headers: dict[str, str], event_payload
) -> None:
    created = client.post(EVENTS_URL, json=event_payload(), headers=organizador_headers).json()
    response = client.patch(
        f"{EVENTS_URL}/{created['id']}",
        json={"name": "Nuevo Nombre"},
        headers=organizador_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Nuevo Nombre"


def test_organizador_cannot_update_other_organizadors_event(
    client: TestClient, make_user, event_payload
) -> None:
    _, token_a = make_user(role="organizador", email="a@example.com")
    _, token_b = make_user(role="organizador", email="b@example.com")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    created = client.post(EVENTS_URL, json=event_payload(), headers=headers_a).json()
    response = client.patch(
        f"{EVENTS_URL}/{created['id']}",
        json={"name": "Hijacked"},
        headers=headers_b,
    )
    assert response.status_code == 403


def test_admin_can_update_any_event(
    client: TestClient, organizador_headers, admin_headers, event_payload
) -> None:
    created = client.post(EVENTS_URL, json=event_payload(), headers=organizador_headers).json()
    response = client.patch(
        f"{EVENTS_URL}/{created['id']}",
        json={"location": "Medellin"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["location"] == "Medellin"


# ============================================
# DELETE (solo borrador)
# ============================================


def test_delete_draft_event_works(
    client: TestClient, organizador_headers, event_payload
) -> None:
    created = client.post(EVENTS_URL, json=event_payload(), headers=organizador_headers).json()
    response = client.delete(f"{EVENTS_URL}/{created['id']}", headers=organizador_headers)
    assert response.status_code == 204

    # Verifica que ya no existe
    follow = client.get(f"{EVENTS_URL}/{created['id']}")
    assert follow.status_code == 404


def test_delete_published_event_returns_409(
    client: TestClient, organizador_headers, event_payload
) -> None:
    created = _create_and_publish(client, organizador_headers, "Live", event_payload)
    response = client.delete(f"{EVENTS_URL}/{created['id']}", headers=organizador_headers)
    assert response.status_code == 409
    assert response.json()["error"] == "event_not_in_draft"


# ============================================
# STATE TRANSITIONS (publish, cancel)
# ============================================


def test_publish_draft_event_works(
    client: TestClient, organizador_headers, event_payload
) -> None:
    created = client.post(EVENTS_URL, json=event_payload(), headers=organizador_headers).json()
    response = client.post(
        f"{EVENTS_URL}/{created['id']}/publish", headers=organizador_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "publicado"


def test_publish_cancelled_event_returns_409(
    client: TestClient, organizador_headers, event_payload
) -> None:
    created = client.post(EVENTS_URL, json=event_payload(), headers=organizador_headers).json()
    client.post(f"{EVENTS_URL}/{created['id']}/cancel", headers=organizador_headers)
    response = client.post(
        f"{EVENTS_URL}/{created['id']}/publish", headers=organizador_headers
    )
    assert response.status_code == 409
    assert response.json()["error"] == "invalid_transition"


def test_cancel_published_event_works(
    client: TestClient, organizador_headers, event_payload
) -> None:
    published = _create_and_publish(client, organizador_headers, "Live", event_payload)
    response = client.post(
        f"{EVENTS_URL}/{published['id']}/cancel", headers=organizador_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelado"


def test_update_finalized_event_blocked(
    client: TestClient,
    organizador_headers,
    event_payload,
    session,
) -> None:
    """Si forzamos finalizado en DB, el update debe ser bloqueado."""
    import uuid

    from mis_eventos.models.event import Event, EventStatus

    created = client.post(EVENTS_URL, json=event_payload(), headers=organizador_headers).json()
    # Forzar finalizado en DB directamente
    db_event = session.get(Event, uuid.UUID(created["id"]))
    db_event.status = EventStatus.FINALIZADO
    session.add(db_event)
    session.commit()

    response = client.patch(
        f"{EVENTS_URL}/{created['id']}",
        json={"name": "Cant change"},
        headers=organizador_headers,
    )
    assert response.status_code == 409
    assert response.json()["error"] == "event_finalized"
