"""Schemas Pydantic para ponentes."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SpeakerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    bio: str = Field(default="", max_length=2000)
    email: EmailStr | None = None


class SpeakerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    bio: str | None = Field(default=None, max_length=2000)
    email: EmailStr | None = None


class SpeakerResponse(BaseModel):
    id: uuid.UUID
    name: str
    bio: str
    email: str | None
    created_at: datetime
