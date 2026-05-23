"""Modelo Event - representa un evento del sistema con su estado."""

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class EventStatus(StrEnum):
    """Estados del evento (state machine).

    Transiciones validas:
        borrador -> publicado, cancelado
        publicado -> cancelado, finalizado
        cancelado, finalizado -> (terminales, no se vuelve atras)
    """

    BORRADOR = "borrador"
    PUBLICADO = "publicado"
    CANCELADO = "cancelado"
    FINALIZADO = "finalizado"


class Event(SQLModel, table=True):
    """Evento con sesiones programadas."""

    __tablename__ = "event"
    __table_args__ = (
        Index("ix_event_status", "status"),
        Index("ix_event_start_date", "start_date"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=200, nullable=False, index=True)
    description: str = Field(default="", max_length=2000)
    start_date: datetime = Field(nullable=False)
    end_date: datetime = Field(nullable=False)
    location: str = Field(default="", max_length=200)
    capacity: int = Field(nullable=False, ge=1)
    status: EventStatus = Field(default=EventStatus.BORRADOR, nullable=False)
    organizer_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
