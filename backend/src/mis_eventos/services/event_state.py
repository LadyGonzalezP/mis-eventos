"""State machine de eventos - logica pura, sin DB.

Transiciones validas:
    borrador  -> publicado | cancelado
    publicado -> cancelado | finalizado
    cancelado -> (terminal)
    finalizado -> (terminal)

Esta logica vive en un servicio separado para ser:
- Testeable sin DB ni HTTP
- Reutilizable desde cualquier endpoint
- Defendible en un code review
"""

from mis_eventos.models.event import EventStatus

_TRANSITIONS: dict[EventStatus, set[EventStatus]] = {
    EventStatus.BORRADOR: {EventStatus.PUBLICADO, EventStatus.CANCELADO},
    EventStatus.PUBLICADO: {EventStatus.CANCELADO, EventStatus.FINALIZADO},
    EventStatus.CANCELADO: set(),
    EventStatus.FINALIZADO: set(),
}


def can_transition(current: EventStatus, target: EventStatus) -> bool:
    """Indica si la transicion `current -> target` es valida."""
    return target in _TRANSITIONS[current]


def valid_next_states(current: EventStatus) -> set[EventStatus]:
    """Devuelve el conjunto de estados a los que se puede pasar desde `current`."""
    return _TRANSITIONS[current].copy()


def is_terminal(status: EventStatus) -> bool:
    """Indica si el estado es terminal (no se puede transicionar a otro)."""
    return len(_TRANSITIONS[status]) == 0
