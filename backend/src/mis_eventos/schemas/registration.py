"""Schemas Pydantic para inscripciones."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from mis_eventos.models.event import EventStatus


class RegistrationResponse(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    user_id: uuid.UUID
    registered_at: datetime


class MyEventResponse(BaseModel):
    """Representacion de un evento inscrito (vista 'mis eventos')."""

    event_id: uuid.UUID
    event_name: str
    event_status: EventStatus
    start_date: datetime
    end_date: datetime
    location: str
    registered_at: datetime
