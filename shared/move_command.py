from dataclasses import dataclass

from config.constants import VALID_PIECES


COMMAND_COLORS = {"W", "B"}
FILES = "abcdefgh"
RANKS = "12345678"


class InvalidMoveCommand(ValueError):
    """Raised when a course-style move command string is malformed."""


@dataclass(frozen=True)
class MoveCommand:
    piece_code: str
    source: str
    target: str


def parse_move_command(command):
    """
    Parse a course-style move command such as ``WQe2e5``.

    Format (exactly 6 characters):
        color + kind + source_file + source_rank + target_file + target_rank
        e.g. W Q e 2 e 5
    """
    if not isinstance(command, str):
        raise InvalidMoveCommand("command must be a string")

    if len(command) != 6:
        raise InvalidMoveCommand("command must be exactly 6 characters")

    piece_code = command[0:2]
    source = command[2:4]
    target = command[4:6]

    color = piece_code[0]
    kind = piece_code[1]

    if color not in COMMAND_COLORS:
        raise InvalidMoveCommand(f"invalid piece color: {color!r}")
    if kind not in VALID_PIECES:
        raise InvalidMoveCommand(f"invalid piece kind: {kind!r}")
    if not _is_square(source):
        raise InvalidMoveCommand(f"invalid source square: {source!r}")
    if not _is_square(target):
        raise InvalidMoveCommand(f"invalid target square: {target!r}")

    return MoveCommand(
        piece_code=piece_code,
        source=source,
        target=target,
    )


def _is_square(square):
    return (
        len(square) == 2
        and square[0] in FILES
        and square[1] in RANKS
    )
