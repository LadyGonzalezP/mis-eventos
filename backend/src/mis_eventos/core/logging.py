"""Configuracion de logs estructurados en JSON con structlog.

Cada log incluye automaticamente:
- timestamp ISO 8601
- nivel (info/warn/error)
- evento (mensaje)
- request_id si esta en el contexto

Uso:
    from mis_eventos.core.logging import logger

    logger.info("event_created", event_id=str(event.id), name=event.name)
"""

import logging
import sys
from typing import Any

import structlog

from mis_eventos.core.config import settings


def configure_logging() -> None:
    """Configura structlog para output JSON estructurado."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "mis_eventos") -> Any:
    return structlog.get_logger(name)


logger = structlog.get_logger("mis_eventos")
