"""FastAPI application entrypoint.

Configura:
- Endpoints de sistema (sin prefijo): /health, /docs, /openapi.json
- Endpoints de negocio (con prefijo /api/v1/): se agregan en los siguientes slices
- Exception handlers globales con formato {error, detail, context}
- OpenAPI tags para organizar Swagger UI
- CORS middleware (whitelist desde .env)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mis_eventos.api import auth, health
from mis_eventos.core.config import settings
from mis_eventos.core.exceptions import register_exception_handlers
from mis_eventos.models import User  # noqa: F401 - registra el modelo en SQLModel.metadata

API_V1_PREFIX = "/api/v1"

# OpenAPI tags metadata - organiza los endpoints en Swagger UI
TAGS_METADATA = [
    {"name": "system", "description": "Endpoints de sistema (health, metadata)."},
    {"name": "auth", "description": "Autenticacion y registro de usuarios."},
    {"name": "events", "description": "Gestion de eventos con state machine."},
    {"name": "sessions", "description": "Sesiones dentro de eventos."},
    {"name": "speakers", "description": "Ponentes asignables a sesiones."},
    {"name": "registrations", "description": "Inscripciones de asistentes a eventos."},
    {"name": "users", "description": "Gestion de usuarios (Admin)."},
]


def create_app() -> FastAPI:
    """Factory que construye la aplicacion FastAPI con toda su configuracion."""
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Plataforma web Full Stack para gestion de eventos.\n\n"
            "Reto tecnico Serviinformacion 2026."
        ),
        version=settings.app_version,
        openapi_tags=TAGS_METADATA,
    )

    # CORS - whitelist de origenes desde .env
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Handlers globales con formato {error, detail, context}
    register_exception_handlers(app)

    # --- Endpoints de sistema (sin prefijo /api/v1/) ---
    app.include_router(health.router)

    # --- Endpoints de negocio (prefijo /api/v1/) ---
    app.include_router(auth.router, prefix=API_V1_PREFIX)
    # Se agregaran en los siguientes slices:
    # app.include_router(events.router, prefix=API_V1_PREFIX)
    # app.include_router(sessions.router, prefix=API_V1_PREFIX)
    # app.include_router(speakers.router, prefix=API_V1_PREFIX)
    # app.include_router(registrations.router, prefix=API_V1_PREFIX)
    # app.include_router(users.router, prefix=API_V1_PREFIX)

    return app


app = create_app()
