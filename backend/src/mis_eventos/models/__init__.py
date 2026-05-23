"""Modelos SQLModel - se importan aqui para que Alembic los detecte."""

from mis_eventos.models.event import Event, EventStatus
from mis_eventos.models.registration import Registration
from mis_eventos.models.session import Session
from mis_eventos.models.speaker import Speaker
from mis_eventos.models.user import User, UserRole

__all__ = [
    "Event",
    "EventStatus",
    "Registration",
    "Session",
    "Speaker",
    "User",
    "UserRole",
]
