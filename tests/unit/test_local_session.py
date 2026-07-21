from model.board import Board
from model.piece import Piece
from model.position import Position

from engine.game_engine import GameEngine
from session.local_session import LocalSession


def test_local_session_pump_advances_engine_time():
    engine = GameEngine(Board([[None]]))
    session = LocalSession(engine)

    session.pump(100)

    assert engine._arbiter.get_time() == 100


def test_local_session_select_and_snapshot_reflect_engine_state():
    engine = GameEngine(Board([[Piece("w", "R")]]))
    session = LocalSession(engine)

    session.select(Position(0, 0))

    assert session.get_selected() == Position(0, 0)
    snapshot = session.create_snapshot()
    assert snapshot.selected_cell == Position(0, 0)


def test_local_session_request_move_to_delegates_to_engine():
    board = Board([[Piece("w", "R"), None]])
    engine = GameEngine(board)
    session = LocalSession(engine)

    session.select(Position(0, 0))
    session.request_move_to(Position(0, 1))

    assert session.get_selected() is None
    assert len(engine._arbiter.get_active_moves()) == 1


def test_local_session_request_jump_to_delegates_to_engine():
    engine = GameEngine(Board([[Piece("w", "P")]]))
    session = LocalSession(engine)

    session.request_jump_to(Position(0, 0))

    assert engine.get_board().get(Position(0, 0)) is None


def test_local_session_game_over_reflects_engine():
    engine = GameEngine(Board([[None]]))
    session = LocalSession(engine)

    assert not session.game_over

    engine.set_game_over()

    assert session.game_over
