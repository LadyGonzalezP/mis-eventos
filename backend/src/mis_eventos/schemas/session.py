"""Schemas Pydantic para sesiones."""

import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator


class SessionCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    start_time: datetime
    end_time: datetime
    capacity: int = Field(ge=1)
    speaker_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def end_after_start(self) -> Self:
        if self.end_time <= self.start_time:
            raise ValueError("end_time debe ser posterior a start_time")
        return self


class SessionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    start_time: datetime | None = None
    end_time: datetime | None = None
    capacity: int | None = Field(default=None, ge=1)
    speaker_id: uuid.UUID | None = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    capacity: int
    speaker_id: uuid.UUID | None
