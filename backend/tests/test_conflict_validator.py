"""Tests del algoritmo de validacion de conflictos de horario.

Cubre los 8+ casos del SPEC SS 4.4:
- No solapamiento -> OK
- Sesiones consecutivas (end == start) -> OK
- Solapamiento total -> conflicto
- Solapamiento parcial (al inicio o al final) -> conflicto
- Sesion nueva contenida en otra -> conflicto
- Sesion existente contenida en la nueva -> conflicto
- Mismo horario distinto ponente -> OK
- Edit excluye la propia sesion -> OK
"""

import uuid
from datetime import datetime

import pytest
from sqlmodel import Session as DbSession

from mis_eventos.models.event import Event, EventStatus
from mis_eventos.models.session import Session
from mis_eventos.models.speaker import Speaker
from mis_eventos.services import conflict_validator


@pytest.fixture(name="speaker_id")
def speaker_id_fixture(session: DbSession) -> uuid.UUID:
    speaker = Speaker(name="Juan Perez")
    session.add(speaker)
    session.commit()
    session.refresh(speaker)
    return speaker.id


@pytest.fixture(name="event_id")
def event_id_fixture(session: DbSession) -> uuid.UUID:
    """Crea un evento dummy para satisfacer la FK de Session.event_id."""
    from mis_eventos.models.user import User, UserRole

    user = User(
        name="Org",
        email="org_conflict@example.com",
        password_hash="x",
        role=UserRole.ORGANIZADOR,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    event = Event(
        name="Test Event",
        start_date=datetime(2030, 6, 1, 8, 0),
        end_date=datetime(2030, 6, 1, 20, 0),
        capacity=100,
        organizer_id=user.id,
        status=EventStatus.PUBLICADO,
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event.id


def _create_session(
    db: DbSession,
    event_id: uuid.UUID,
    speaker_id: uuid.UUID | None,
    start: datetime,
    end: datetime,
    title: str = "Test Session",
) -> Session:
    s = Session(
        event_id=event_id,
        title=title,
        start_time=start,
        end_time=end,
        capacity=50,
        speaker_id=speaker_id,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ============================================
# Casos del SPEC SS 4.4
# ============================================


def test_no_overlap_passes(
    session: DbSession, speaker_id: uuid.UUID, event_id: uuid.UUID
) -> None:
    """Sesiones en distintos horarios -> sin conflicto."""
    _create_session(
        session,
        event_id,
        speaker_id,
        datetime(2030, 6, 1, 9, 0),
        datetime(2030, 6, 1, 10, 0),
    )
    conflict = conflict_validator.find_conflict(
        session,
        speaker_id,
        datetime(2030, 6, 1, 14, 0),
        datetime(2030, 6, 1, 15, 0),
    )
    assert conflict is None


def test_consecutive_sessions_pass(
    session: DbSession, speaker_id: uuid.UUID, event_id: uuid.UUID
) -> None:
    """end_time == start_time -> no se solapan (intervalo semi-abierto)."""
    _create_session(
        session,
        event_id,
        speaker_id,
        datetime(2030, 6, 1, 9, 0),
        datetime(2030, 6, 1, 10, 0),
    )
    conflict = conflict_validator.find_conflict(
        session,
        speaker_id,
        datetime(2030, 6, 1, 10, 0),  # arranca justo cuando la otra termina
        datetime(2030, 6, 1, 11, 0),
    )
    assert conflict is None


def test_total_overlap_fails(
    session: DbSession, speaker_id: uuid.UUID, event_id: uuid.UUID
) -> None:
    """Mismas horas exactas -> conflicto."""
    _create_session(
        session,
        event_id,
        speaker_id,
        datetime(2030, 6, 1, 9, 0),
        datetime(2030, 6, 1, 10, 0),
    )
    conflict = conflict_validator.find_conflict(
        session,
        speaker_id,
        datetime(2030, 6, 1, 9, 0),
        datetime(2030, 6, 1, 10, 0),
    )
    assert conflict is not None


def test_partial_overlap_at_start_fails(
    session: DbSession, speaker_id: uuid.UUID, event_id: uuid.UUID
) -> None:
    """Nueva sesion empieza antes y se solapa con el inicio de la otra."""
    _create_session(
        session,
        event_id,
        speaker_id,
        datetime(2030, 6, 1, 10, 0),
        datetime(2030, 6, 1, 11, 0),
    )
    conflict = conflict_validator.find_conflict(
        session,
        speaker_id,
        datetime(2030, 6, 1, 9, 30),
        datetime(2030, 6, 1, 10, 30),
    )
    assert conflict is not None


def test_partial_overlap_at_end_fails(
    session: DbSession, speaker_id: uuid.UUID, event_id: uuid.UUID
) -> None:
    """Nueva sesion empieza durante la otra y termina despues."""
    _create_session(
        session,
        event_id,
        speaker_id,
        datetime(2030, 6, 1, 10, 0),
        datetime(2030, 6, 1, 11, 0),
    )
    conflict = conflict_validator.find_conflict(
        session,
        speaker_id,
        datetime(2030, 6, 1, 10, 30),
        datetime(2030, 6, 1, 11, 30),
    )
    assert conflict is not None


def test_new_inside_existing_fails(
    session: DbSession, speaker_id: uuid.UUID, event_id: uuid.UUID
) -> None:
    """Nueva sesion contenida dentro de otra existente."""
    _create_session(
        session,
        event_id,
        speaker_id,
        datetime(2030, 6, 1, 9, 0),
        datetime(2030, 6, 1, 12, 0),
    )
    conflict = conflict_validator.find_conflict(
        session,
        speaker_id,
        datetime(2030, 6, 1, 10, 0),
        datetime(2030, 6, 1, 11, 0),
    )
    assert conflict is not None


def test_existing_inside_new_fails(
    session: DbSession, speaker_id: uuid.UUID, event_id: uuid.UUID
) -> None:
    """Sesion existente esta contenida en la nueva (nueva es mas larga)."""
    _create_session(
        session,
        event_id,
        speaker_id,
        datetime(2030, 6, 1, 10, 0),
        datetime(2030, 6, 1, 11, 0),
    )
    conflict = conflict_validator.find_conflict(
        session,
        speaker_id,
        datetime(2030, 6, 1, 9, 0),
        datetime(2030, 6, 1, 12, 0),
    )
    assert conflict is not None


def test_same_time_different_speakers_pass(
    session: DbSession, event_id: uuid.UUID
) -> None:
    """Dos ponentes distintos pueden tener sesiones simultaneas."""
    speaker1 = Speaker(name="Speaker 1")
    speaker2 = Speaker(name="Speaker 2")
    session.add(speaker1)
    session.add(speaker2)
    session.commit()
    session.refresh(speaker1)
    session.refresh(speaker2)

    _create_session(
        session,
        event_id,
        speaker1.id,
        datetime(2030, 6, 1, 10, 0),
        datetime(2030, 6, 1, 11, 0),
    )
    conflict = conflict_validator.find_conflict(
        session,
        speaker2.id,
        datetime(2030, 6, 1, 10, 0),
        datetime(2030, 6, 1, 11, 0),
    )
    assert conflict is None


def test_edit_session_excludes_self(
    session: DbSession, speaker_id: uuid.UUID, event_id: uuid.UUID
) -> None:
    """Al editar una sesion no debe chocar consigo misma."""
    existing = _create_session(
        session,
        event_id,
        speaker_id,
        datetime(2030, 6, 1, 10, 0),
        datetime(2030, 6, 1, 11, 0),
    )
    # Editar a otro horario pero con la misma session_id en exclude
    conflict = conflict_validator.find_conflict(
        session,
        speaker_id,
        datetime(2030, 6, 1, 10, 0),
        datetime(2030, 6, 1, 11, 0),
        exclude_session_id=existing.id,
    )
    assert conflict is None


def test_no_speaker_no_conflict(
    session: DbSession, event_id: uuid.UUID
) -> None:
    """Sesion sin ponente -> no se puede tener conflicto (find no se llama)."""
    speaker = Speaker(name="Free")
    session.add(speaker)
    session.commit()

    # Solo verificamos que con speaker_id=None no falla nada (caller debe skip)
    # Aqui pasamos un id que no tiene sesiones - debe devolver None
    conflict = conflict_validator.find_conflict(
        session,
        speaker.id,
        datetime(2030, 6, 1, 10, 0),
        datetime(2030, 6, 1, 11, 0),
    )
    assert conflict is None


@pytest.mark.parametrize(
    ("new_start", "new_end", "should_conflict"),
    [
        # No solapamientos
        ((2030, 6, 1, 8, 0), (2030, 6, 1, 9, 0), False),   # antes
        ((2030, 6, 1, 12, 0), (2030, 6, 1, 13, 0), False),  # despues
        ((2030, 6, 1, 11, 0), (2030, 6, 1, 12, 0), False),  # exactamente despues (end == start)
        # Solapamientos
        ((2030, 6, 1, 9, 30), (2030, 6, 1, 10, 30), True),  # inicio
        ((2030, 6, 1, 10, 30), (2030, 6, 1, 11, 30), True),  # final
        ((2030, 6, 1, 10, 15), (2030, 6, 1, 10, 45), True),  # dentro
        ((2030, 6, 1, 9, 0), (2030, 6, 1, 12, 0), True),    # envolvente
        ((2030, 6, 1, 10, 0), (2030, 6, 1, 11, 0), True),    # exacto
    ],
)
def test_conflict_matrix(
    session: DbSession,
    speaker_id: uuid.UUID,
    event_id: uuid.UUID,
    new_start: tuple,
    new_end: tuple,
    should_conflict: bool,
) -> None:
    """Matriz exhaustiva de combinaciones de horario."""
    _create_session(
        session,
        event_id,
        speaker_id,
        datetime(2030, 6, 1, 10, 0),
        datetime(2030, 6, 1, 11, 0),
    )
    conflict = conflict_validator.find_conflict(
        session,
        speaker_id,
        datetime(*new_start),
        datetime(*new_end),
    )
    if should_conflict:
        assert conflict is not None, f"Esperaba conflicto en {new_start} - {new_end}"
    else:
        assert conflict is None, f"NO esperaba conflicto en {new_start} - {new_end}"
