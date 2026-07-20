import pytest

from shared.move_command import InvalidMoveCommand, MoveCommand, parse_move_command


def test_parse_valid_command():
    result = parse_move_command("WQe2e5")

    assert result == MoveCommand(
        piece_code="WQ",
        source="e2",
        target="e5",
    )


def test_parse_rejects_too_short():
    with pytest.raises(InvalidMoveCommand, match="exactly 6"):
        parse_move_command("WQe2e")


def test_parse_rejects_too_long():
    with pytest.raises(InvalidMoveCommand, match="exactly 6"):
        parse_move_command("WQe2e5x")


def test_parse_rejects_invalid_source():
    with pytest.raises(InvalidMoveCommand, match="source"):
        parse_move_command("WQz2e5")


def test_parse_rejects_invalid_target():
    with pytest.raises(InvalidMoveCommand, match="target"):
        parse_move_command("WQe2i5")


def test_parse_rejects_invalid_piece_code():
    with pytest.raises(InvalidMoveCommand, match="piece"):
        parse_move_command("WXe2e5")


def test_parse_rejects_lowercase_color():
    with pytest.raises(InvalidMoveCommand, match="color"):
        parse_move_command("wQe2e5")
