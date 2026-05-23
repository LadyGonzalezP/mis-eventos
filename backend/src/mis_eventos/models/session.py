"""Modelo Session - charla/actividad dentro de un evento."""

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Session(SQLModel, table=True):
    """Sesion dentro de un evento.

    speaker_id es nullable (ON DELETE SET NULL en speaker delete).
    event_id es CASCADE (sesiones se borran si el evento se borra).
    """

    __tablename__ = "session"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    event_id: uuid.UUID = Field(
        foreign_key="event.id",
        nullable=False,
        sa_column_kwargs={"index": True},
    )
    title: str = Field(max_length=200, nullable=False)
    description: str = Field(default="", max_length=2000)
    start_time: datetime = Field(nullable=False, index=True)
    end_time: datetime = Field(nullable=False)
    speaker_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="speaker.id",
        sa_column_kwargs={"index": True},
    )
    capacity: int = Field(nullable=False, ge=1)
