from config.constants import JUMP_DURATION
from engine.game_engine import GameEngine
from model.board import Board
from model.piece import Piece
from model.piece_state import PieceState
from model.position import Position


def test_jump_in_place_from_starting_square():
    rook = Piece("W", "R")
    source = Position(0, 0)

    board = Board([[rook]])
    engine = GameEngine(board)

    engine.jump(source)

    assert board.get(source) is None
    assert len(engine._arbiter.get_active_jumps()) == 1
    assert rook.state == PieceState.JUMP

    snapshot = engine.create_snapshot()
    jump_pieces = [p for p in snapshot.pieces if p.state == PieceState.JUMP]
    assert len(jump_pieces) == 1
    assert jump_pieces[0].position == source

    engine.tick(JUMP_DURATION)

    assert board.get(source) is rook
    assert rook.state == PieceState.SHORT_REST


def test_jump_in_place_after_move():
    rook = Piece("W", "R")
    source = Position(0, 0)
    target = Position(0, 1)
    move_duration = 100

    board = Board([[rook, None]])
    engine = GameEngine(board)

    assert board.get(source) is rook

    engine.select(source)
    engine.move_request(target)
    engine.tick(move_duration)

    assert board.get(source) is None
    assert board.get(target) is rook

    engine.jump(target)

    assert board.get(target) is None
    active_jumps = engine._arbiter.get_active_jumps()
    assert len(active_jumps) == 1
    assert active_jumps[0].position == target
    assert rook.state == PieceState.JUMP

    snapshot = engine.create_snapshot()
    jump_pieces = [p for p in snapshot.pieces if p.state == PieceState.JUMP]
    assert len(jump_pieces) == 1
    assert jump_pieces[0].position == target

    engine.tick(JUMP_DURATION)

    assert board.get(target) is rook
    assert rook.state == PieceState.SHORT_REST
