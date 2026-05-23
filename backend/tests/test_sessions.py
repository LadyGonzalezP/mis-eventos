"""Tests de endpoints de sesiones - integracion con conflict validator."""

from typing import Any

from fastapi.testclient import TestClient

EVENTS_URL = "/api/v1/events"
SPEAKERS_URL = "/api/v1/speakers"
SESSIONS_URL = "/api/v1/sessions"


def _create_event(
    client: TestClient, headers, event_payload, name: str = "Event"
) -> dict[str, Any]:
    return client.post(EVENTS_URL, json=event_payload(name=name), headers=headers).json()


def _create_speaker(client: TestClient, headers, name: str = "Juan Perez") -> dict[str, Any]:
    return client.post(SPEAKERS_URL, json={"name": name, "bio": "bio"}, headers=headers).json()


def _session_payload(speaker_id: str | None = None) -> dict[str, Any]:
    return {
        "title": "Charla X",
        "description": "desc",
        "start_time": "2030-06-01T10:00:00",
        "end_time": "2030-06-01T11:00:00",
        "capacity": 50,
        "speaker_id": speaker_id,
    }


# ============================================
# Crear sesion
# ============================================


def test_create_session_without_speaker_works(
    client: TestClient, organizador_headers, event_payload
) -> None:
    event = _create_event(client, organizador_headers, event_payload)
    response = client.post(
        f"{EVENTS_URL}/{event['id']}/sessions",
        json=_session_payload(),
        headers=organizador_headers,
    )
    assert response.status_code == 201
    assert response.json()["speaker_id"] is None


def test_create_session_with_speaker_works(
    client: TestClient, organizador_headers, event_payload
) -> None:
    event = _create_event(client, organizador_headers, event_payload)
    speaker = _create_speaker(client, organizador_headers)
    response = client.post(
        f"{EVENTS_URL}/{event['id']}/sessions",
        json=_session_payload(speaker_id=speaker["id"]),
        headers=organizador_headers,
    )
    assert response.status_code == 201
    assert response.json()["speaker_id"] == speaker["id"]


def test_create_session_with_conflicting_speaker_returns_409(
    client: TestClient, organizador_headers, event_payload
) -> None:
    """Misma sesion exacta con mismo ponente -> conflicto."""
    event = _create_event(client, organizador_headers, event_payload)
    speaker = _create_speaker(client, organizador_headers)

    # Primera sesion OK
    client.post(
        f"{EVENTS_URL}/{event['id']}/sessions",
        json=_session_payload(speaker_id=speaker["id"]),
        headers=organizador_headers,
    )
    # Segunda misma horario y ponente -> 409
    response = client.post(
        f"{EVENTS_URL}/{event['id']}/sessions",
        json=_session_payload(speaker_id=speaker["id"]),
        headers=organizador_headers,
    )
    assert response.status_code == 409
    data = response.json()
    assert data["error"] == "schedule_conflict"
    assert "session_id" in data["context"]
    assert "event_name" in data["context"]


def test_create_session_outside_event_range_returns_400(
    client: TestClient, organizador_headers, event_payload
) -> None:
    event = _create_event(client, organizador_headers, event_payload)
    payload = _session_payload()
    payload["start_time"] = "2030-05-30T10:00:00"  # Antes del evento
    payload["end_time"] = "2030-05-30T11:00:00"
    response = client.post(
        f"{EVENTS_URL}/{event['id']}/sessions",
        json=payload,
        headers=organizador_headers,
    )
    assert response.status_code == 400
    assert response.json()["error"] == "session_out_of_event_range"


def test_create_session_capacity_exceeding_event_returns_400(
    client: TestClient, organizador_headers, event_payload
) -> None:
    event = _create_event(client, organizador_headers, event_payload)
    payload = _session_payload()
    payload["capacity"] = 500  # Evento es de 100
    response = client.post(
        f"{EVENTS_URL}/{event['id']}/sessions",
        json=payload,
        headers=organizador_headers,
    )
    assert response.status_code == 400


def test_asistente_cannot_create_session(
    client: TestClient,
    organizador_headers,
    asistente_headers,
    event_payload,
) -> None:
    event = _create_event(client, organizador_headers, event_payload)
    response = client.post(
        f"{EVENTS_URL}/{event['id']}/sessions",
        json=_session_payload(),
        headers=asistente_headers,
    )
    assert response.status_code == 403


# ============================================
# Editar sesion
# ============================================


def test_edit_session_without_changing_time_does_not_conflict_with_itself(
    client: TestClient, organizador_headers, event_payload
) -> None:
    """Al editar sin cambiar horario, no debe chocar consigo misma."""
    event = _create_event(client, organizador_headers, event_payload)
    speaker = _create_speaker(client, organizador_headers)
    created = client.post(
        f"{EVENTS_URL}/{event['id']}/sessions",
        json=_session_payload(speaker_id=speaker["id"]),
        headers=organizador_headers,
    ).json()

    # Editar solo el titulo
    response = client.patch(
        f"{SESSIONS_URL}/{created['id']}",
        json={"title": "Nuevo titulo"},
        headers=organizador_headers,
    )
    assert response.status_code == 200


# ============================================
# Speaker delete - sesiones quedan con NULL
# ============================================


def test_delete_speaker_nullifies_session_speaker_id(
    client: TestClient,
    organizador_headers,
    admin_headers,
    event_payload,
) -> None:
    event = _create_event(client, organizador_headers, event_payload)
    speaker = _create_speaker(client, organizador_headers)
    session = client.post(
        f"{EVENTS_URL}/{event['id']}/sessions",
        json=_session_payload(speaker_id=speaker["id"]),
        headers=organizador_headers,
    ).json()

    # Borrar ponente (solo admin)
    delete_response = client.delete(f"{SPEAKERS_URL}/{speaker['id']}", headers=admin_headers)
    assert delete_response.status_code == 204

    # Verificar que la sesion ahora tiene speaker_id NULL
    follow = client.get(f"{SESSIONS_URL}/{session['id']}")
    assert follow.status_code == 200
    assert follow.json()["speaker_id"] is None
