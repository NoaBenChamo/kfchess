from model.position import Position
from model.piece_state import PieceState

from client.client_state import ClientState
from client.snapshot_codec import (
    piece_at,
    snapshot_dict_to_game_snapshot,
)


def _sample_snapshot(sequence=0):
    return {
        "sequence": sequence,
        "board_width": 8,
        "board_height": 8,
        "game_over": False,
        "white_score": 0,
        "black_score": 0,
        "white_moves": [],
        "black_moves": [],
        "pieces": [
            {
                "color": "w",
                "piece_type": "P",
                "row": 6,
                "col": 4,
                "state": "idle",
            }
        ],
    }


def test_snapshot_dict_to_game_snapshot_builds_view_objects():
    snapshot = snapshot_dict_to_game_snapshot(_sample_snapshot(), selected_cell=Position(6, 4))
    assert snapshot.board_width == 8
    assert snapshot.selected_cell == Position(6, 4)
    assert len(snapshot.pieces) == 1
    assert snapshot.pieces[0].piece_type == "P"
    assert snapshot.pieces[0].state == PieceState.IDLE


def test_client_state_ignores_stale_sequence():
    state = ClientState()
    state.handle_message({"type": "state_snapshot", "payload": _sample_snapshot(2)})
    state.handle_message({"type": "state_snapshot", "payload": _sample_snapshot(1)})
    assert state.sequence == 2


def test_client_state_move_accepted_clears_selection():
    state = ClientState()
    state.select(Position(6, 4))
    state.handle_message({
        "type": "move_accepted",
        "payload": {"command": "WPe2e4", "snapshot": _sample_snapshot(1)},
    })
    assert state.selected is None
    assert state.sequence == 1


def test_piece_at_finds_piece():
    data = _sample_snapshot()
    assert piece_at(data, Position(6, 4)) == ("w", "P")
    assert piece_at(data, Position(0, 0)) is None


def test_client_state_identity_assigned_stores_color():
    state = ClientState()
    state.handle_message({
        "type": "identity_assigned",
        "payload": {
            "username": "Noa",
            "color": "b",
            "game_id": "default",
        },
    })

    assert state.username == "Noa"
    assert state.assigned_color == "b"
    assert state.ready is False

    state.handle_message({
        "type": "state_snapshot",
        "payload": _sample_snapshot(),
    })
    assert state.ready is True
