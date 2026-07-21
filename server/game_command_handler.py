from shared.move_command import InvalidMoveCommand, parse_move_command
from shared.protocol import NOT_YOUR_PIECE
from shared.squares import square_to_position
from server.snapshot_serializer import snapshot_to_dict


class GameCommandHandler:
    """
    Applies parsed network commands to a Match's GameEngine.
    """

    def apply_move_command(self, match, command_text, assigned_color=None):
        try:
            command = parse_move_command(command_text)
        except InvalidMoveCommand as exc:
            return {
                "ok": False,
                "error_code": "invalid_move_command",
                "error_message": str(exc),
            }

        expected_color = command.piece_code[0].lower()
        expected_kind = command.piece_code[1]

        if assigned_color is not None and expected_color != assigned_color:
            return {
                "ok": False,
                "error_code": NOT_YOUR_PIECE,
                "error_message": "cannot move opponent pieces",
            }

        source = square_to_position(command.source)
        target = square_to_position(command.target)
        engine = match.engine
        board = engine.get_board()
        piece = board.get(source)

        if piece is None:
            return {
                "ok": False,
                "error_code": "INVALID_MOVE",
                "error_message": "no piece at source",
            }

        if piece.color.lower() != expected_color or piece.type != expected_kind:
            return {
                "ok": False,
                "error_code": "INVALID_MOVE",
                "error_message": "piece code does not match board",
            }

        accepted = engine.move_from_to(source, target)
        if not accepted:
            return {
                "ok": False,
                "error_code": "INVALID_MOVE",
                "error_message": "move rejected by engine",
            }

        # Time advances via Match tick loop (B.3), not per-client.
        match._last_state_key = match._state_key()
        sequence = match.bump_sequence()
        snapshot = snapshot_to_dict(engine.create_snapshot(), sequence=sequence)

        return {
            "ok": True,
            "command": command_text,
            "snapshot": snapshot,
        }
