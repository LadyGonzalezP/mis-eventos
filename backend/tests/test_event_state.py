"""Tests del state machine de eventos - logica pura, sin DB."""

import pytest

from mis_eventos.models.event import EventStatus
from mis_eventos.services import event_state


class TestCanTransition:
    """Transiciones validas e invalidas del state machine."""

    def test_borrador_to_publicado_valid(self) -> None:
        assert event_state.can_transition(EventStatus.BORRADOR, EventStatus.PUBLICADO) is True

    def test_borrador_to_cancelado_valid(self) -> None:
        assert event_state.can_transition(EventStatus.BORRADOR, EventStatus.CANCELADO) is True

    def test_borrador_to_finalizado_invalid(self) -> None:
        assert event_state.can_transition(EventStatus.BORRADOR, EventStatus.FINALIZADO) is False

    def test_publicado_to_cancelado_valid(self) -> None:
        assert event_state.can_transition(EventStatus.PUBLICADO, EventStatus.CANCELADO) is True

    def test_publicado_to_finalizado_valid(self) -> None:
        assert event_state.can_transition(EventStatus.PUBLICADO, EventStatus.FINALIZADO) is True

    def test_publicado_to_borrador_invalid(self) -> None:
        assert event_state.can_transition(EventStatus.PUBLICADO, EventStatus.BORRADOR) is False

    def test_cancelado_is_terminal(self) -> None:
        for target in EventStatus:
            assert event_state.can_transition(EventStatus.CANCELADO, target) is False

    def test_finalizado_is_terminal(self) -> None:
        for target in EventStatus:
            assert event_state.can_transition(EventStatus.FINALIZADO, target) is False


class TestValidNextStates:
    def test_borrador_can_go_to_publicado_and_cancelado(self) -> None:
        nexts = event_state.valid_next_states(EventStatus.BORRADOR)
        assert nexts == {EventStatus.PUBLICADO, EventStatus.CANCELADO}

    def test_publicado_can_go_to_cancelado_and_finalizado(self) -> None:
        nexts = event_state.valid_next_states(EventStatus.PUBLICADO)
        assert nexts == {EventStatus.CANCELADO, EventStatus.FINALIZADO}

    def test_terminal_states_have_no_next(self) -> None:
        assert event_state.valid_next_states(EventStatus.CANCELADO) == set()
        assert event_state.valid_next_states(EventStatus.FINALIZADO) == set()

    def test_returned_set_is_a_copy(self) -> None:
        """No se debe poder mutar el set interno del state machine."""
        nexts = event_state.valid_next_states(EventStatus.BORRADOR)
        nexts.add(EventStatus.FINALIZADO)
        # El siguiente call debe devolver el original sin la mutacion
        fresh = event_state.valid_next_states(EventStatus.BORRADOR)
        assert EventStatus.FINALIZADO not in fresh


class TestIsTerminal:
    def test_cancelado_is_terminal(self) -> None:
        assert event_state.is_terminal(EventStatus.CANCELADO) is True

    def test_finalizado_is_terminal(self) -> None:
        assert event_state.is_terminal(EventStatus.FINALIZADO) is True

    def test_borrador_is_not_terminal(self) -> None:
        assert event_state.is_terminal(EventStatus.BORRADOR) is False

    def test_publicado_is_not_terminal(self) -> None:
        assert event_state.is_terminal(EventStatus.PUBLICADO) is False


@pytest.mark.parametrize(
    ("current", "target", "expected"),
    [
        (EventStatus.BORRADOR, EventStatus.PUBLICADO, True),
        (EventStatus.BORRADOR, EventStatus.CANCELADO, True),
        (EventStatus.BORRADOR, EventStatus.FINALIZADO, False),
        (EventStatus.PUBLICADO, EventStatus.CANCELADO, True),
        (EventStatus.PUBLICADO, EventStatus.FINALIZADO, True),
        (EventStatus.PUBLICADO, EventStatus.BORRADOR, False),
        (EventStatus.CANCELADO, EventStatus.PUBLICADO, False),
        (EventStatus.FINALIZADO, EventStatus.PUBLICADO, False),
    ],
)
def test_state_machine_matrix(
    current: EventStatus, target: EventStatus, expected: bool
) -> None:
    """Matriz completa de transiciones."""
    assert event_state.can_transition(current, target) is expected
