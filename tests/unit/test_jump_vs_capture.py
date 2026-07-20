from config.constants import JUMP_DURATION
from engine.game_engine import GameEngine
from model.board import Board
from model.piece import Piece
from model.piece_state import PieceState
from model.position import Position
from realtime.jump import Jump
from realtime.move import Move
from realtime.real_time_arbiter import RealTimeArbiter


def _jumping_rook_vs_attacking_rook_scenario():
    jumper = Piece("w", "R")
    attacker = Piece("b", "R")
    square = Position(0, 0)
    attacker_source = Position(0, 2)
    move_duration = 200
    move_start = 500

    board = Board([
        [jumper, None, attacker],
    ])
    engine = GameEngine(board)

    engine.jump(square)
    engine._arbiter.add_move(Move(
        attacker,
        attacker_source,
        square,
        start_time=move_start,
        duration=move_duration,
    ))

    return engine, board, jumper, attacker, square, move_start, move_duration


def test_jump_survives_enemy_capture_attempt():
    engine, board, jumper, attacker, square, move_start, move_duration = (
        _jumping_rook_vs_attacking_rook_scenario()
    )

    engine.tick(move_start)
    assert len(engine._arbiter.get_active_jumps()) == 1
    assert jumper.state == PieceState.JUMP
    assert board.get(square) is None

    engine.tick(move_duration)

    active_jumps = engine._arbiter.get_active_jumps()
    assert len(active_jumps) == 1
    assert active_jumps[0].captured_piece is attacker
    assert board.get(square) is None
    assert board.get(Position(0, 2)) is None
    assert jumper.state == PieceState.JUMP

    snapshot = engine.create_snapshot()
    jump_pieces = [p for p in snapshot.pieces if p.state == PieceState.JUMP]
    assert len(jump_pieces) == 1
    assert jump_pieces[0].position == square

    engine.tick(JUMP_DURATION - move_start - move_duration)

    assert board.get(square) is jumper
    assert jumper.state == PieceState.SHORT_REST


def test_attacker_captures_jumper_after_jump_lands():
    square = Position(0, 0)
    board = Board([[Piece("w", "R"), None, Piece("b", "R")]])
    engine = GameEngine(board)
    jumper = board.get(square)
    attacker = board.get(Position(0, 2))

    engine.jump(square)
    engine._arbiter.add_move(Move(
        attacker,
        Position(0, 2),
        square,
        start_time=500,
        duration=501,
    ))

    engine.tick(1001)

    assert board.get(square) is attacker
    assert jumper not in [piece for row in board.get_rows() for piece in row if piece]


def test_regular_capture_still_works():
    attacker = Piece("w", "R")
    defender = Piece("b", "R")
    attacker_source = Position(0, 0)
    defender_square = Position(0, 1)

    board = Board([[attacker, defender]])
    engine = GameEngine(board)

    engine.select(attacker_source)
    engine.move_request(defender_square)
    engine.tick(100)

    assert board.get(attacker_source) is None
    assert board.get(defender_square) is attacker
    assert defender_square not in {
        p.position for p in engine.create_snapshot().pieces
        if p.piece_type == "R" and p.color == "b"
    }


def test_jump_blocks_friendly_piece_arrival():
    jumper = Piece("w", "R")
    friend = Piece("w", "N")
    square = Position(0, 0)
    friend_source = Position(0, 2)

    board = Board([[jumper, None, friend]])
    arbiter = RealTimeArbiter(board)

    arbiter.add_jump(Jump(square, jumper, start_time=0, duration=JUMP_DURATION))
    board.set(square, None)

    arbiter.add_move(Move(
        friend,
        friend_source,
        square,
        start_time=500,
        duration=200,
    ))

    arbiter.tick(700)

    assert len(arbiter.get_active_moves()) == 0
    assert board.get(square) is None
    assert board.get(Position(0, 1)) is friend
    assert board.get(friend_source) is None
    assert friend.state == PieceState.LONG_REST
    assert len(arbiter.get_active_jumps()) == 1
    assert arbiter.get_active_jumps()[0].piece is jumper

    arbiter.tick(JUMP_DURATION - 700)

    assert board.get(square) is jumper
    assert board.get(Position(0, 1)) is friend
    assert jumper.state == PieceState.SHORT_REST


def test_two_non_jump_pieces_behave_as_before():
    mover = Piece("w", "R")
    blocker = Piece("b", "R")
    source = Position(0, 0)
    target = Position(0, 1)

    board = Board([[mover, blocker]])
    arbiter = RealTimeArbiter(board)

    arbiter.add_move(Move(mover, source, target, start_time=0, duration=100))
    arbiter.tick(100)

    assert board.get(source) is None
    assert board.get(target) is mover
    assert blocker not in board.get_rows()[0]
