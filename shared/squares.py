from model.position import Position

FILES = "abcdefgh"
RANKS = "12345678"


def square_to_position(square):
    """
    Convert algebraic square (e.g. e2) to board Position.

    Row 0 is rank 8 (top / black back rank); row 7 is rank 1.
    """
    if len(square) != 2 or square[0] not in FILES or square[1] not in RANKS:
        raise ValueError(f"invalid square: {square!r}")
    col = FILES.index(square[0])
    row = 8 - int(square[1])
    return Position(row, col)


def position_to_square(position):
    return FILES[position.col] + RANKS[7 - position.row]
