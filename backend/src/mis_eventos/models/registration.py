"""Modelo Registration - inscripcion de un User a un Event (M:N)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Registration(SQLModel, table=True):
    """Inscripcion de un usuario a un evento.

    UNIQUE(event_id, user_id) - un usuario no puede inscribirse 2 veces al mismo evento.
    """

    __tablename__ = "registration"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_registration_event_user"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    event_id: uuid.UUID = Field(
        foreign_key="event.id", nullable=False, sa_column_kwargs={"index": True}
    )
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, sa_column_kwargs={"index": True}
    )
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
