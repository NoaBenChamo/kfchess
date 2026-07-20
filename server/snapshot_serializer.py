def snapshot_to_dict(snapshot, sequence=0):
    """Convert GameSnapshot to a JSON-serializable dict."""
    return {
        "sequence": sequence,
        "board_width": snapshot.board_width,
        "board_height": snapshot.board_height,
        "game_over": snapshot.game_over,
        "selected_cell": _position_to_dict(snapshot.selected_cell),
        "white_score": snapshot.white_score,
        "black_score": snapshot.black_score,
        "pieces": [_piece_to_dict(piece) for piece in snapshot.pieces],
        "white_moves": [_move_to_dict(move) for move in snapshot.white_moves],
        "black_moves": [_move_to_dict(move) for move in snapshot.black_moves],
    }


def _position_to_dict(position):
    if position is None:
        return None
    return {"row": position.row, "col": position.col}


def _piece_to_dict(piece):
    data = {
        "color": piece.color,
        "piece_type": piece.piece_type,
        "row": piece.position.row,
        "col": piece.position.col,
        "state": piece.state.value if hasattr(piece.state, "value") else piece.state,
    }
    if piece.target is not None:
        data["target_row"] = piece.target.row
        data["target_col"] = piece.target.col
    if piece.progress is not None:
        data["progress"] = piece.progress
    if piece.rest_progress is not None:
        data["rest_progress"] = piece.rest_progress
    return data


def _move_to_dict(move):
    return {
        "color": move.color,
        "piece_type": move.piece_type,
        "source": _position_to_dict(move.source),
        "target": _position_to_dict(move.target),
        "move_type": move.move_type,
        "time_ms": move.time_ms,
    }
