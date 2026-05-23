"""Validacion de conflictos de horario de ponentes.

Un mismo ponente no puede dar dos sesiones que se solapan en el tiempo,
sin importar si son del mismo evento o de eventos distintos.

Algoritmo (interval overlap):
    Dos intervalos [a, b) y [c, d) se solapan si y solo si:
        a < d  AND  b > c

Esto es O(n) sobre las sesiones existentes del ponente. Para corpus grandes
una mejora futura seria un indice GIST de PostgreSQL con tstzrange.
"""

import uuid
from datetime import datetime

from sqlmodel import Session as DbSession
from sqlmodel import select

from mis_eventos.models.session import Session


def find_conflict(
    db: DbSession,
    speaker_id: uuid.UUID,
    start_time: datetime,
    end_time: datetime,
    exclude_session_id: uuid.UUID | None = None,
) -> Session | None:
    """Busca una sesion del ponente que se solape con el rango dado.

    Args:
        db: sesion de DB
        speaker_id: ID del ponente cuya agenda chequear
        start_time, end_time: rango propuesto para la nueva sesion
        exclude_session_id: ID a excluir (usar en UPDATE - excluye la propia sesion)

    Returns:
        La primera Session que choca, o None si no hay conflicto.
    """
    stmt = select(Session).where(
        Session.speaker_id == speaker_id,
        Session.start_time < end_time,
        Session.end_time > start_time,
    )
    if exclude_session_id is not None:
        stmt = stmt.where(Session.id != exclude_session_id)

    return db.exec(stmt).first()
