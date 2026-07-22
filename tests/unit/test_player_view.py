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

    assert format_move_notation(record) == "JUMP b6"


def test_player_view_display_rating_reads_snapshot_fields():
    from snapshots.game_snapshot import GameSnapshot
    from view.hud.player_view import PlayerView

    snapshot = GameSnapshot(
        board_width=8,
        board_height=8,
        pieces=[],
        selected_cell=None,
        game_over=False,
        white_username="Alice",
        black_username="Bob",
        white_rating=1200,
        black_rating=1250,
    )
    white = PlayerView("white")
    black = PlayerView("black")

    assert white._display_rating(snapshot) == 1200
    assert black._display_rating(snapshot) == 1250
    assert white._display_rating(GameSnapshot(8, 8, [], None, False)) is None
