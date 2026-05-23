"""Endpoint de health check.

Verifica que el servicio HTTP y la conexion a la base de datos esten vivos.
Se usa para:
- Probes de Docker / Kubernetes / load balancers
- Monitoreo externo
- Smoke test post-deploy

No usa prefijo /api/v1/ porque es un endpoint de sistema, no de negocio.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from mis_eventos.core.config import settings
from mis_eventos.db.session import get_db

router = APIRouter(tags=["system"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("/health")
def health_check(db: DbDep) -> dict[str, Any]:
    """Reporta el estado del servicio y la conexion a la base de datos.

    Siempre devuelve 200 OK (el endpoint en si esta vivo si responde).
    El campo `db` indica si la conexion a la DB esta funcionando.
    """
    try:
        db.exec(text("SELECT 1"))  # type: ignore[call-overload]
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
        "version": settings.app_version,
    }
