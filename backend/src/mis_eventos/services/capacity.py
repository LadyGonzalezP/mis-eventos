"""Servicio de control de cupos de eventos."""

import uuid

from sqlmodel import Session as DbSession
from sqlmodel import func, select

from mis_eventos.models.event import Event
from mis_eventos.models.registration import Registration


def count_registrations(db: DbSession, event_id: uuid.UUID) -> int:
    """Cuenta cuantos asistentes hay inscritos a un evento."""
    stmt = select(func.count()).select_from(Registration).where(
        Registration.event_id == event_id
    )
    return db.exec(stmt).one()


def available_slots(db: DbSession, event_id: uuid.UUID) -> int:
    """Devuelve cupos disponibles (capacity - inscritos). Min 0."""
    event = db.get(Event, event_id)
    if not event:
        return 0
    return max(0, event.capacity - count_registrations(db, event_id))


def is_user_registered(db: DbSession, event_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Indica si el usuario ya esta inscrito al evento."""
    stmt = select(Registration).where(
        Registration.event_id == event_id, Registration.user_id == user_id
    )
    return db.exec(stmt).first() is not None
