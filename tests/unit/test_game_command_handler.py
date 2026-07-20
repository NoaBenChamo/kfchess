from server.game_command_handler import GameCommandHandler
from server.match import Match


def test_apply_legal_pawn_move_returns_snapshot():
    match = Match("default")
    handler = GameCommandHandler()

    result = handler.apply_move_command(match, "WPe2e4")

    assert result["ok"] is True
    assert result["command"] == "WPe2e4"
    snapshot = result["snapshot"]
    assert snapshot["sequence"] == 1
    assert snapshot["board_width"] == 8
    assert any(
        piece["piece_type"] == "P"
        and piece["color"] == "w"
        and piece["state"] == "move"
        and piece.get("target_row") == 4
        and piece.get("target_col") == 4
        for piece in snapshot["pieces"]
    )


def test_apply_rejects_wrong_piece_code():
    match = Match("default")
    handler = GameCommandHandler()

    result = handler.apply_move_command(match, "WQe2e4")

    assert result["ok"] is False
    assert result["error_code"] == "INVALID_MOVE"


def test_apply_rejects_illegal_move():
    match = Match("default")
    handler = GameCommandHandler()

    result = handler.apply_move_command(match, "WPe2e5")

    assert result["ok"] is False
    assert result["error_code"] == "INVALID_MOVE"
