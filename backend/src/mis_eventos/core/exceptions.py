"""Manejo centralizado de errores con formato estandar.

Todas las excepciones de la app heredan de `AppError`. El handler las traduce
a respuestas HTTP con el formato consistente definido en SPEC.md SS 6:

    {
        "error": "machine_readable_code",
        "detail": "Mensaje legible en espanol",
        "context": {}
    }

Esto permite que el frontend muestre mensajes legibles y que se puedan
mapear errores de forma programatica.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Excepcion base de la aplicacion con formato de respuesta estandar."""

    def __init__(
        self,
        error: str,
        detail: str,
        status_code: int = 400,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.error = error
        self.detail = detail
        self.status_code = status_code
        self.context = context or {}
        super().__init__(detail)


# --- Errores especificos de dominio (se iran agregando por slice) ---


class ForbiddenError(AppError):
    """403 - El usuario no tiene permisos para esta accion."""

    def __init__(self, detail: str = "No tienes permisos para realizar esta accion") -> None:
        super().__init__(error="forbidden", detail=detail, status_code=403)


class NotFoundError(AppError):
    """404 - Recurso no encontrado."""

    def __init__(self, detail: str = "Recurso no encontrado") -> None:
        super().__init__(error="not_found", detail=detail, status_code=404)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los handlers globales en la app FastAPI."""

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error, "detail": exc.detail, "context": exc.context},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"http_{exc.status_code}",
                "detail": str(exc.detail),
                "context": {},
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": "Los datos enviados no son validos",
                "context": {"errors": exc.errors()},
            },
        )
