from model.position import Position

from snapshots.move_record import MoveRecord
from view.hud.player_view import format_move_notation, format_move_time


def test_format_move_time():
    assert format_move_time(2889) == "00:02.889"
    assert format_move_time(4902) == "00:04.902"
    assert format_move_time(6636) == "00:06.636"
    assert format_move_time(None) == ""


def test_format_move_notation_for_pawn():
    record = MoveRecord("w", "P", Position(6, 5), Position(4, 5))

    assert format_move_notation(record) == "f4"


def test_format_move_notation_for_piece():
    record = MoveRecord("w", "Q", Position(6, 3), Position(4, 6))

    assert format_move_notation(record) == "Qg4"


def test_format_move_notation_for_jump():
    record = MoveRecord("w", "N", Position(2, 1), Position(2, 1), "jump")

    assert format_move_notation(record) == "→"
