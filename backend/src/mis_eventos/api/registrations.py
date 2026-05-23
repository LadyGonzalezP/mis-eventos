"""Endpoints de inscripciones - registro a eventos + 'mis eventos'."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select

from mis_eventos.core.exceptions import AppError, NotFoundError
from mis_eventos.core.security import CurrentUser
from mis_eventos.db.session import get_db
from mis_eventos.models.event import Event, EventStatus
from mis_eventos.models.registration import Registration
from mis_eventos.schemas.registration import MyEventResponse, RegistrationResponse
from mis_eventos.services import capacity

# Router para POST/DELETE /events/{id}/register
event_register_router = APIRouter(tags=["registrations"])

# Router para GET /me/registrations
me_router = APIRouter(prefix="/me", tags=["registrations"])

DbDep = Annotated[Session, Depends(get_db)]


@event_register_router.post(
    "/events/{event_id}/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_to_event(
    event_id: uuid.UUID, db: DbDep, current_user: CurrentUser
) -> RegistrationResponse:
    """Inscribe al usuario actual al evento (si esta publicado y hay cupo)."""
    event = db.get(Event, event_id)
    if not event:
        raise NotFoundError(detail="Evento no encontrado")

    if event.status != EventStatus.PUBLICADO:
        raise AppError(
            error="event_not_open_for_registration",
            detail="Solo se puede inscribir a eventos publicados",
            status_code=400,
            context={"current_status": event.status.value},
        )

    if capacity.is_user_registered(db, event_id, current_user.id):
        raise AppError(
            error="already_registered",
            detail="Ya estas inscrito a este evento",
            status_code=409,
        )

    if capacity.available_slots(db, event_id) <= 0:
        raise AppError(
            error="event_full",
            detail="El evento esta lleno - no hay cupos disponibles",
            status_code=409,
            context={"available_slots": 0, "capacity": event.capacity},
        )

    registration = Registration(event_id=event_id, user_id=current_user.id)
    db.add(registration)
    db.commit()
    db.refresh(registration)

    return RegistrationResponse(
        id=registration.id,
        event_id=registration.event_id,
        user_id=registration.user_id,
        registered_at=registration.registered_at,
    )


@event_register_router.delete(
    "/events/{event_id}/register",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cancel_registration(
    event_id: uuid.UUID, db: DbDep, current_user: CurrentUser
) -> None:
    """Cancela la propia inscripcion al evento."""
    stmt = select(Registration).where(
        Registration.event_id == event_id, Registration.user_id == current_user.id
    )
    registration = db.exec(stmt).first()
    if not registration:
        raise NotFoundError(detail="No estas inscrito a este evento")

    db.delete(registration)
    db.commit()


@me_router.get("/registrations", response_model=list[MyEventResponse])
def my_registrations(db: DbDep, current_user: CurrentUser) -> list[MyEventResponse]:
    """Lista los eventos a los que estoy inscrito (con estado actual)."""
    stmt = (
        select(Registration, Event)
        .join(Event, Registration.event_id == Event.id)
        .where(Registration.user_id == current_user.id)
        .order_by(Event.start_date)
    )
    results = db.exec(stmt).all()

    return [
        MyEventResponse(
            event_id=event.id,
            event_name=event.name,
            event_status=event.status,
            start_date=event.start_date,
            end_date=event.end_date,
            location=event.location,
            registered_at=registration.registered_at,
        )
        for registration, event in results
    ]
