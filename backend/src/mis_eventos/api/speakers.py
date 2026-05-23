"""Endpoints de ponentes (Speakers)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select

from mis_eventos.core.exceptions import NotFoundError
from mis_eventos.core.security import CurrentUser, require_role
from mis_eventos.db.session import get_db
from mis_eventos.models.speaker import Speaker
from mis_eventos.models.user import UserRole
from mis_eventos.schemas.speaker import SpeakerCreate, SpeakerResponse, SpeakerUpdate

router = APIRouter(prefix="/speakers", tags=["speakers"])

DbDep = Annotated[Session, Depends(get_db)]
AuthenticatedDep = Depends(require_role(UserRole.ASISTENTE, UserRole.ORGANIZADOR, UserRole.ADMIN))
OrganizerOrAdminDep = Depends(require_role(UserRole.ORGANIZADOR, UserRole.ADMIN))
AdminOnlyDep = Depends(require_role(UserRole.ADMIN))


def _to_response(speaker: Speaker) -> SpeakerResponse:
    return SpeakerResponse(
        id=speaker.id,
        name=speaker.name,
        bio=speaker.bio,
        email=speaker.email,
        created_at=speaker.created_at,
    )


@router.get("", response_model=list[SpeakerResponse], dependencies=[AuthenticatedDep])
def list_speakers(db: DbDep) -> list[SpeakerResponse]:
    speakers = db.exec(select(Speaker).order_by(Speaker.name)).all()
    return [_to_response(s) for s in speakers]


@router.post(
    "",
    response_model=SpeakerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[OrganizerOrAdminDep],
)
def create_speaker(payload: SpeakerCreate, db: DbDep) -> SpeakerResponse:
    speaker = Speaker(name=payload.name, bio=payload.bio, email=payload.email)
    db.add(speaker)
    db.commit()
    db.refresh(speaker)
    return _to_response(speaker)


@router.get(
    "/{speaker_id}",
    response_model=SpeakerResponse,
    dependencies=[AuthenticatedDep],
)
def get_speaker(speaker_id: uuid.UUID, db: DbDep) -> SpeakerResponse:
    speaker = db.get(Speaker, speaker_id)
    if not speaker:
        raise NotFoundError(detail="Ponente no encontrado")
    return _to_response(speaker)


@router.patch(
    "/{speaker_id}",
    response_model=SpeakerResponse,
    dependencies=[AdminOnlyDep],
)
def update_speaker(
    speaker_id: uuid.UUID, payload: SpeakerUpdate, db: DbDep, _current: CurrentUser
) -> SpeakerResponse:
    speaker = db.get(Speaker, speaker_id)
    if not speaker:
        raise NotFoundError(detail="Ponente no encontrado")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(speaker, key, value)
    db.add(speaker)
    db.commit()
    db.refresh(speaker)
    return _to_response(speaker)


@router.delete(
    "/{speaker_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[AdminOnlyDep],
)
def delete_speaker(speaker_id: uuid.UUID, db: DbDep, _current: CurrentUser) -> None:
    """Elimina un ponente. Sus sesiones quedan con speaker_id=NULL."""
    from mis_eventos.models.session import Session as SessionModel

    speaker = db.get(Speaker, speaker_id)
    if not speaker:
        raise NotFoundError(detail="Ponente no encontrado")

    # Limpia las referencias (SQLite no soporta ON DELETE SET NULL por default)
    sessions = db.exec(select(SessionModel).where(SessionModel.speaker_id == speaker_id)).all()
    for s in sessions:
        s.speaker_id = None
        db.add(s)

    db.delete(speaker)
    db.commit()
