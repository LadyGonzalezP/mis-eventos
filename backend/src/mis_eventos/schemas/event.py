"""Schemas Pydantic para eventos."""

import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator

from mis_eventos.models.event import EventStatus


class EventCreate(BaseModel):
    """Body de POST /events."""

    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    start_date: datetime
    end_date: datetime
    location: str = Field(default="", max_length=200)
    capacity: int = Field(ge=1)

    @model_validator(mode="after")
    def end_after_start(self) -> Self:
        if self.end_date <= self.start_date:
            raise ValueError("end_date debe ser posterior a start_date")
        return self


class EventUpdate(BaseModel):
    """Body de PATCH /events/{id} - todos los campos opcionales."""

    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    start_date: datetime | None = None
    end_date: datetime | None = None
    location: str | None = Field(default=None, max_length=200)
    capacity: int | None = Field(default=None, ge=1)


class EventResponse(BaseModel):
    """Respuesta de detalle/listado de eventos."""

    id: uuid.UUID
    name: str
    description: str
    start_date: datetime
    end_date: datetime
    location: str
    capacity: int
    status: EventStatus
    organizer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    """Respuesta paginada de GET /events."""

    items: list[EventResponse]
    total: int
    page: int
    limit: int
