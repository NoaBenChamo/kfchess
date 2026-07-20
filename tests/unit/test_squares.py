import pytest

from shared.squares import position_to_square, square_to_position
from model.position import Position


def test_square_to_position_e2():
    assert square_to_position("e2") == Position(6, 4)


def test_square_to_position_a8():
    assert square_to_position("a8") == Position(0, 0)


def test_position_roundtrip():
    for square in ("a1", "h8", "e4", "d5"):
        assert position_to_square(square_to_position(square)) == square
