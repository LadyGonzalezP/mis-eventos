"""Endpoint bonus de IA - generacion de descripciones desde el titulo."""

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from mis_eventos.core.exceptions import AppError
from mis_eventos.core.security import require_role
from mis_eventos.llm.provider import get_llm
from mis_eventos.models.user import UserRole
from mis_eventos.services.description_generator import generate_event_description

router = APIRouter(prefix="/ai", tags=["ai"])

OrganizerOrAdminDep = Depends(require_role(UserRole.ORGANIZADOR, UserRole.ADMIN))


class GenerateDescriptionRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)


class GenerateDescriptionResponse(BaseModel):
    description: str


@router.post(
    "/generate-description",
    response_model=GenerateDescriptionResponse,
    dependencies=[OrganizerOrAdminDep],
    summary="Genera una descripcion del evento a partir del titulo (Bonus IA)",
)
def generate_description(payload: GenerateDescriptionRequest) -> GenerateDescriptionResponse:
    """Usa Groq + Llama 3.3 para generar una descripcion (150-250 palabras)."""
    try:
        llm = get_llm()
    except ValueError as exc:
        raise AppError(
            error="llm_not_configured",
            detail="La generacion con IA no esta disponible (GROQ_API_KEY no configurada)",
            status_code=503,
        ) from exc

    try:
        description = generate_event_description(llm, payload.title)
    except (httpx.HTTPError, KeyError, IndexError) as exc:
        raise AppError(
            error="llm_request_failed",
            detail="El proveedor de IA fallo al generar la descripcion",
            status_code=502,
        ) from exc

    return GenerateDescriptionResponse(description=description)
