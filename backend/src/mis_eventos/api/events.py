"""Endpoints de eventos - CRUD + state machine (publish/cancel)."""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session, func, select

from mis_eventos.core.exceptions import AppError, ForbiddenError, NotFoundError
from mis_eventos.core.security import CurrentUser, require_role
from mis_eventos.db.session import get_db
from mis_eventos.models.event import Event, EventStatus
from mis_eventos.models.user import UserRole
from mis_eventos.schemas.event import (
    EventCreate,
    EventListResponse,
    EventResponse,
    EventUpdate,
)
from mis_eventos.services import event_state

router = APIRouter(prefix="/events", tags=["events"])

DbDep = Annotated[Session, Depends(get_db)]
OrganizerOrAdmin = Depends(require_role(UserRole.ORGANIZADOR, UserRole.ADMIN))


def _to_response(event: Event) -> EventResponse:
    return EventResponse(
        id=event.id,
        name=event.name,
        description=event.description,
        start_date=event.start_date,
        end_date=event.end_date,
        location=event.location,
        capacity=event.capacity,
        status=event.status,
        organizer_id=event.organizer_id,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


def _ensure_can_edit(event: Event, user) -> None:
    if user.role == UserRole.ADMIN:
        return
    if event.organizer_id != user.id:
        raise ForbiddenError(detail="Solo el organizador o un Admin puede editar este evento")


# ============================================
# CREATE
# ============================================


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[OrganizerOrAdmin],
)
def create_event(
    payload: EventCreate, db: DbDep, current_user: CurrentUser
) -> EventResponse:
    """Crea un evento en estado `borrador`."""
    event = Event(
        name=payload.name,
        description=payload.description,
        start_date=payload.start_date,
        end_date=payload.end_date,
        location=payload.location,
        capacity=payload.capacity,
        status=EventStatus.BORRADOR,
        organizer_id=current_user.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _to_response(event)


# ============================================
# LIST + SEARCH
# ============================================


@router.get("", response_model=EventListResponse)
def list_events(
    db: DbDep,
    q: Annotated[str | None, Query(description="Busqueda parcial por nombre")] = None,
    event_status: Annotated[EventStatus | None, Query(alias="status")] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> EventListResponse:
    """Listado publico de eventos publicados (con filtros + paginacion).

    No requiere auth. Solo devuelve eventos en estado `publicado` salvo que
    se pase un filtro explicito de status (que solo aplican Admins).
    """
    stmt = select(Event)

    if event_status is None:
        stmt = stmt.where(Event.status == EventStatus.PUBLICADO)
    else:
        stmt = stmt.where(Event.status == event_status)

    if q:
        like_pattern = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(Event.name).like(like_pattern))

    if date_from:
        stmt = stmt.where(Event.start_date >= date_from)
    if date_to:
        stmt = stmt.where(Event.start_date <= date_to)

    # Conteo total (sin offset/limit)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.exec(count_stmt).one()

    # Paginacion + orden
    offset = (page - 1) * limit
    stmt = stmt.order_by(Event.start_date).offset(offset).limit(limit)
    events = db.exec(stmt).all()

    return EventListResponse(
        items=[_to_response(e) for e in events],
        total=total,
        page=page,
        limit=limit,
    )


# ============================================
# DETAIL
# ============================================


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: uuid.UUID, db: DbDep) -> EventResponse:
    """Detalle publico del evento (cualquier estado)."""
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(detail="Evento no encontrado")
    return _to_response(event)


# ============================================
# UPDATE
# ============================================


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    dependencies=[OrganizerOrAdmin],
)
def update_event(
    event_id: uuid.UUID,
    payload: EventUpdate,
    db: DbDep,
    current_user: CurrentUser,
) -> EventResponse:
    """Actualiza un evento. Solo dueno o Admin. No se permite si finalizado."""
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(detail="Evento no encontrado")

    _ensure_can_edit(event, current_user)

    if event.status == EventStatus.FINALIZADO:
        raise AppError(
            error="event_finalized",
            detail="No se puede editar un evento finalizado",
            status_code=409,
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)

    # Validar end > start si cualquiera cambio
    if event.end_date <= event.start_date:
        raise AppError(
            error="invalid_dates",
            detail="end_date debe ser posterior a start_date",
            status_code=400,
        )

    event.updated_at = datetime.now(UTC)
    db.add(event)
    db.commit()
    db.refresh(event)
    return _to_response(event)


# ============================================
# DELETE (solo borrador)
# ============================================


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[OrganizerOrAdmin],
)
def delete_event(
    event_id: uuid.UUID, db: DbDep, current_user: CurrentUser
) -> None:
    """Elimina un evento. Solo si esta en `borrador`."""
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(detail="Evento no encontrado")

    _ensure_can_edit(event, current_user)

    if event.status != EventStatus.BORRADOR:
        raise AppError(
            error="event_not_in_draft",
            detail="Solo se pueden eliminar eventos en estado borrador. Usa cancelar.",
            status_code=409,
            context={"current_status": event.status.value},
        )

    db.delete(event)
    db.commit()


# ============================================
# STATE TRANSITIONS (publish, cancel)
# ============================================


def _transition_status(
    event: Event, target: EventStatus, db: Session
) -> Event:
    """Aplica una transicion validada por el state machine."""
    if not event_state.can_transition(event.status, target):
        raise AppError(
            error="invalid_transition",
            detail=f"No se puede pasar de {event.status.value} a {target.value}",
            status_code=409,
            context={
                "from": event.status.value,
                "to": target.value,
                "valid_next": [s.value for s in event_state.valid_next_states(event.status)],
            },
        )
    event.status = target
    event.updated_at = datetime.now(UTC)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post(
    "/{event_id}/publish",
    response_model=EventResponse,
    dependencies=[OrganizerOrAdmin],
)
def publish_event(
    event_id: uuid.UUID, db: DbDep, current_user: CurrentUser
) -> EventResponse:
    """Cambia el estado a `publicado` (visible para asistentes)."""
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(detail="Evento no encontrado")
    _ensure_can_edit(event, current_user)
    event = _transition_status(event, EventStatus.PUBLICADO, db)
    return _to_response(event)


@router.post(
    "/{event_id}/cancel",
    response_model=EventResponse,
    dependencies=[OrganizerOrAdmin],
)
def cancel_event(
    event_id: uuid.UUID, db: DbDep, current_user: CurrentUser
) -> EventResponse:
    """Cancela el evento (terminal, no se vuelve atras)."""
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(detail="Evento no encontrado")
    _ensure_can_edit(event, current_user)
    event = _transition_status(event, EventStatus.CANCELADO, db)
    return _to_response(event)
