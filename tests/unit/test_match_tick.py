import asyncio

import pytest

from model.piece_state import PieceState
from server.game_command_handler import GameCommandHandler
from server.game_registry import GameRegistry
from server.match import Match
from shared.squares import square_to_position


@pytest.mark.asyncio
async def test_match_tick_completes_pawn_move_without_client_messages():
    match = Match("solo")
    handler = GameCommandHandler()

    async with match.lock:
        result = handler.apply_move_command(match, "WPe2e4")
    assert result["ok"] is True

    await match.start_tick_loop(tick_ms=20)
    await asyncio.sleep(0.4)
    await match.stop()

    board = match.engine.get_board()
    piece = board.get(square_to_position("e4"))
    assert piece is not None
    assert piece.type == "P"
    assert piece.color == "w"
    assert piece.state != PieceState.MOVE

    assert board.get(square_to_position("e2")) is None


@pytest.mark.asyncio
async def test_two_matches_tick_independently():
    match_a = Match("a")
    match_b = Match("b")
    handler = GameCommandHandler()

    async with match_a.lock:
        assert handler.apply_move_command(match_a, "WPe2e4")["ok"]

    await match_a.start_tick_loop(20)
    await match_b.start_tick_loop(20)
    await asyncio.sleep(0.4)
    await match_a.stop()
    await match_b.stop()

    assert match_a.engine.get_board().get(square_to_position("e4")) is not None
    assert match_b.engine.get_board().get(square_to_position("e2")) is not None
    assert match_b.engine.get_board().get(square_to_position("e4")) is None


@pytest.mark.asyncio
async def test_stop_cancels_tick_task():
    match = Match("x")
    await match.start_tick_loop(50)
    assert match.tick_running is True
    await match.stop()
    assert match.tick_running is False


@pytest.mark.asyncio
async def test_registry_matches_are_isolated_units():
    registry = GameRegistry()
    registry.register(Match("g1"))
    registry.register(Match("g2"))
    assert len(registry) == 2
    assert {m.game_id for m in registry.all_matches()} == {"g1", "g2"}
