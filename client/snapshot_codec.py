from model.piece_state import PieceState
from model.position import Position
from snapshots.game_snapshot import GameSnapshot
from snapshots.move_record import MoveRecord
from snapshots.piece_snapshot import PieceSnapshot


def snapshot_dict_to_game_snapshot(data, selected_cell=None):
    """Rebuild a view-layer GameSnapshot from a network snapshot dict."""
    pieces = [_piece_from_dict(piece) for piece in data.get("pieces", [])]
    return GameSnapshot(
        board_width=data.get("board_width", 0),
        board_height=data.get("board_height", 0),
        pieces=pieces,
        selected_cell=selected_cell,
        game_over=bool(data.get("game_over", False)),
        white_moves=[_move_from_dict(m) for m in data.get("white_moves", [])],
        black_moves=[_move_from_dict(m) for m in data.get("black_moves", [])],
        white_score=data.get("white_score", 0),
        black_score=data.get("black_score", 0),
    )


def _piece_from_dict(data):
    target = None
    if "target_row" in data and "target_col" in data:
        target = Position(data["target_row"], data["target_col"])
    state = data.get("state", "idle")
    if not isinstance(state, PieceState):
        state = PieceState(state)
    return PieceSnapshot(
        data["color"],
        data["piece_type"],
        Position(data["row"], data["col"]),
        state,
        target=target,
        progress=data.get("progress"),
        rest_progress=data.get("rest_progress"),
    )


def _move_from_dict(data):
    source = data.get("source") or {}
    target = data.get("target") or {}
    return MoveRecord(
        data["color"],
        data["piece_type"],
        Position(source["row"], source["col"]),
        Position(target["row"], target["col"]),
        move_type=data.get("move_type", "move"),
        time_ms=data.get("time_ms"),
    )


def piece_at(snapshot_dict, position):
    """Return (color, piece_type) for a stationary or moving piece at position."""
    if snapshot_dict is None:
        return None
    for piece in snapshot_dict.get("pieces", []):
        if piece["row"] == position.row and piece["col"] == position.col:
            return piece["color"], piece["piece_type"]
    return None
