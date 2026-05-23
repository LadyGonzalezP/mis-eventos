"""Modelo Speaker - ponente reutilizable entre eventos."""

import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Speaker(SQLModel, table=True):
    """Ponente. Puede dar sesiones en multiples eventos."""

    __tablename__ = "speaker"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, nullable=False, index=True)
    bio: str = Field(default="", max_length=2000)
    email: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
