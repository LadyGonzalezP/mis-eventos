"""Endpoints de sesiones - CRUD + validacion de conflictos de horario."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel import Session as DbSession
from sqlmodel import select

from mis_eventos.core.exceptions import AppError, ForbiddenError, NotFoundError
from mis_eventos.core.security import CurrentUser, require_role
from mis_eventos.db.session import get_db
from mis_eventos.models.event import Event
from mis_eventos.models.session import Session
from mis_eventos.models.speaker import Speaker
from mis_eventos.models.user import UserRole
from mis_eventos.schemas.session import SessionCreate, SessionResponse, SessionUpdate
from mis_eventos.services import conflict_validator

# Router para /events/{event_id}/sessions (anidado)
event_sessions_router = APIRouter(tags=["sessions"])

# Router para /sessions/{id} (operaciones por ID)
sessions_router = APIRouter(prefix="/sessions", tags=["sessions"])

DbDep = Annotated[DbSession, Depends(get_db)]
OrganizerOrAdminDep = Depends(require_role(UserRole.ORGANIZADOR, UserRole.ADMIN))


def _to_response(session: Session) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        event_id=session.event_id,
        title=session.title,
        description=session.description,
        start_time=session.start_time,
        end_time=session.end_time,
        capacity=session.capacity,
        speaker_id=session.speaker_id,
    )


def _ensure_event_editable(event: Event, user) -> None:
    if user.role == UserRole.ADMIN:
        return
    if event.organizer_id != user.id:
        raise ForbiddenError(
            detail="Solo el organizador del evento o un Admin puede gestionar sus sesiones"
        )


def _validate_session_in_event_range(
    event: Event, start_time, end_time
) -> None:
    if start_time < event.start_date or end_time > event.end_date:
        raise AppError(
            error="session_out_of_event_range",
            detail="La sesion debe estar dentro del rango de fechas del evento",
            status_code=400,
            context={
                "event_start": event.start_date.isoformat(),
                "event_end": event.end_date.isoformat(),
            },
        )


def _validate_capacity_le_event(event: Event, capacity: int) -> None:
    if capacity > event.capacity:
        raise AppError(
            error="session_capacity_exceeds_event",
            detail=(
                f"La capacidad de la sesion ({capacity}) "
                f"no puede superar la del evento ({event.capacity})"
            ),
            status_code=400,
        )


def _validate_no_conflict(
    db: DbSession,
    speaker_id: uuid.UUID | None,
    start_time,
    end_time,
    exclude_session_id: uuid.UUID | None = None,
) -> None:
    if speaker_id is None:
        return

    conflict = conflict_validator.find_conflict(
        db, speaker_id, start_time, end_time, exclude_session_id
    )
    if conflict:
        # Obtener nombre del ponente y del evento para mensaje claro
        speaker = db.get(Speaker, speaker_id)
        conflict_event = db.get(Event, conflict.event_id)
        speaker_name = speaker.name if speaker else ""
        raise AppError(
            error="schedule_conflict",
            detail=f"El ponente {speaker_name} ya tiene una sesion en ese horario",
            status_code=409,
            context={
                "session_id": str(conflict.id),
                "event_name": conflict_event.name if conflict_event else None,
                "start_time": conflict.start_time.isoformat(),
                "end_time": conflict.end_time.isoformat(),
            },
        )


# ============================================
# Sesiones por evento
# ============================================


@event_sessions_router.get(
    "/events/{event_id}/sessions", response_model=list[SessionResponse]
)
def list_event_sessions(event_id: uuid.UUID, db: DbDep) -> list[SessionResponse]:
    """Lista las sesiones de un evento (publico)."""
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(detail="Evento no encontrado")

    sessions = db.exec(
        select(Session)
        .where(Session.event_id == event_id)
        .order_by(Session.start_time)
    ).all()
    return [_to_response(s) for s in sessions]


@event_sessions_router.post(
    "/events/{event_id}/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[OrganizerOrAdminDep],
)
def create_session(
    event_id: uuid.UUID,
    payload: SessionCreate,
    db: DbDep,
    current_user: CurrentUser,
) -> SessionResponse:
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(detail="Evento no encontrado")

    _ensure_event_editable(event, current_user)
    _validate_session_in_event_range(event, payload.start_time, payload.end_time)
    _validate_capacity_le_event(event, payload.capacity)
    _validate_no_conflict(db, payload.speaker_id, payload.start_time, payload.end_time)

    if payload.speaker_id is not None:
        if db.get(Speaker, payload.speaker_id) is None:
            raise NotFoundError(detail="Ponente no encontrado")

    session_obj = Session(
        event_id=event_id,
        title=payload.title,
        description=payload.description,
        start_time=payload.start_time,
        end_time=payload.end_time,
        capacity=payload.capacity,
        speaker_id=payload.speaker_id,
    )
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return _to_response(session_obj)


# ============================================
# Sesiones por ID
# ============================================


@sessions_router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: uuid.UUID, db: DbDep) -> SessionResponse:
    session_obj = db.get(Session, session_id)
    if not session_obj:
        raise NotFoundError(detail="Sesion no encontrada")
    return _to_response(session_obj)


@sessions_router.patch(
    "/{session_id}",
    response_model=SessionResponse,
    dependencies=[OrganizerOrAdminDep],
)
def update_session(
    session_id: uuid.UUID,
    payload: SessionUpdate,
    db: DbDep,
    current_user: CurrentUser,
) -> SessionResponse:
    session_obj = db.get(Session, session_id)
    if not session_obj:
        raise NotFoundError(detail="Sesion no encontrada")

    event = db.get(Event, session_obj.event_id)
    _ensure_event_editable(event, current_user)

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session_obj, key, value)

    # Validar end > start
    if session_obj.end_time <= session_obj.start_time:
        raise AppError(
            error="invalid_times",
            detail="end_time debe ser posterior a start_time",
            status_code=400,
        )

    _validate_session_in_event_range(event, session_obj.start_time, session_obj.end_time)
    _validate_capacity_le_event(event, session_obj.capacity)
    _validate_no_conflict(
        db,
        session_obj.speaker_id,
        session_obj.start_time,
        session_obj.end_time,
        exclude_session_id=session_obj.id,
    )

    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return _to_response(session_obj)


@sessions_router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[OrganizerOrAdminDep],
)
def delete_session(
    session_id: uuid.UUID, db: DbDep, current_user: CurrentUser
) -> None:
    session_obj = db.get(Session, session_id)
    if not session_obj:
        raise NotFoundError(detail="Sesion no encontrada")

    event = db.get(Event, session_obj.event_id)
    _ensure_event_editable(event, current_user)

    db.delete(session_obj)
    db.commit()
