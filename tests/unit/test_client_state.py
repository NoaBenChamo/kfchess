from model.position import Position
from model.piece_state import PieceState

from client.client_state import ClientState
from client.snapshot_codec import (
    piece_at,
    snapshot_dict_to_game_snapshot,
)
from server.session_role_enum import SessionRole


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
    assert state.role == SessionRole.PLAYER
    assert state.ready is False

    state.handle_message({
        "type": "state_snapshot",
        "payload": _sample_snapshot(),
    })
    assert state.ready is True


def test_client_state_private_room_waits_for_both_players():
    state = ClientState()
    state.handle_message({
        "type": "room_update",
        "payload": {
            "room_id": "AB12CD",
            "game_id": "g1",
            "players": {"w": {"username": "Alice"}},
            "spectators": [],
            "status": "waiting",
            "role": SessionRole.PLAYER,
            "color": "w",
        },
    })
    state.handle_message({
        "type": "state_snapshot",
        "payload": _sample_snapshot(1),
    })
    assert state.ready is False

    state.handle_message({
        "type": "room_update",
        "payload": {
            "room_id": "AB12CD",
            "game_id": "g1",
            "players": {
                "w": {"username": "Alice"},
                "b": {"username": "Bob"},
            },
            "spectators": [],
            "status": "playing",
        },
    })
    assert state.ready is True
    assert state.player_usernames() == ("Alice", "Bob")
    assert "Private Room AB12CD" in state.hud_line()


def test_client_state_disconnect_notice_in_hud():
    state = ClientState()
    state.handle_message({
        "type": "match_found",
        "payload": {
            "color": "b",
            "game_id": "g1",
            "opponent": {"username": "Alice", "rating": 1200},
        },
    })
    state.handle_message({
        "type": "player_disconnected",
        "payload": {"color": "w", "grace_period_ms": 60_000},
    })
    assert "White disconnected" in state.hud_line()
    assert "60s" in state.hud_line()

    state.handle_message({"type": "player_reconnected", "payload": {"color": "w"}})
    assert "disconnected" not in state.hud_line()


def test_client_state_spectator_ready_without_color():
    state = ClientState()
    state.handle_message({
        "type": "room_update",
        "payload": {
            "room_id": "AB12CD",
            "game_id": "g1",
            "players": {
                "w": {"username": "Alice"},
                "b": {"username": "Bob"},
            },
            "spectators": [{"username": "Carol"}],
            "status": "playing",
            "role": SessionRole.SPECTATOR,
        },
    })
    state.handle_message({
        "type": "state_snapshot",
        "payload": _sample_snapshot(1),
    })
    assert state.role == SessionRole.SPECTATOR
    assert state.assigned_color is None
    assert state.room_id == "AB12CD"
    assert state.ready is True
    assert "Spectator — read only" in state.hud_line()


def test_client_state_ratings_from_match_found_and_game_over():
    state = ClientState()
    state.handle_message({
        "type": "auth_ok",
        "payload": {"user_id": 1, "username": "Alice", "rating": 1200},
    })
    state.handle_message({
        "type": "match_found",
        "payload": {
            "color": "w",
            "game_id": "g1",
            "opponent": {"username": "Bob", "rating": 1250},
        },
    })
    state.handle_message({
        "type": "state_snapshot",
        "payload": _sample_snapshot(1),
    })

    assert state.player_ratings() == (1200, 1250)
    snapshot = state.create_snapshot()
    assert snapshot.white_rating == 1200
    assert snapshot.black_rating == 1250

    state.handle_message({
        "type": "game_over",
        "payload": {
            "winner": "w",
            "ratings": {
                "w": {"rating_after": 1216},
                "b": {"rating_after": 1234},
            },
        },
    })
    assert state.rating == 1216
    assert state.opponent_rating == 1234
    assert state.player_ratings() == (1216, 1234)


def test_client_state_ratings_from_room_players():
    state = ClientState()
    state.handle_message({
        "type": "room_update",
        "payload": {
            "room_id": "AB12CD",
            "game_id": "g1",
            "players": {
                "w": {"username": "Alice", "rating": 1300},
                "b": {"username": "Bob", "rating": 1100},
            },
            "spectators": [],
            "status": "playing",
            "role": SessionRole.PLAYER,
            "color": "w",
        },
    })
    state.handle_message({
        "type": "state_snapshot",
        "payload": _sample_snapshot(1),
    })
    assert state.player_ratings() == (1300, 1100)
    assert state.create_snapshot().white_rating == 1300
    assert state.create_snapshot().black_rating == 1100


def test_matchmaking_waiting_keeps_ready_false_until_match_found():
    state = ClientState()
    state.handle_message({
        "type": "auth_ok",
        "payload": {"user_id": 1, "username": "Alice", "rating": 1200},
    })
    state.handle_message({
        "type": "request_ok",
        "payload": {"status": "waiting"},
    })
    assert state.matchmaking_waiting is True
    assert state.ready is False

    state.handle_message({
        "type": "match_found",
        "payload": {
            "color": "w",
            "game_id": "g1",
            "opponent": {"username": "Bob", "rating": 1210},
        },
    })
    assert state.matchmaking_waiting is False
    assert state.ready is False  # still need snapshot

    state.handle_message({
        "type": "state_snapshot",
        "payload": _sample_snapshot(1),
    })
    assert state.ready is True


def test_matchmaking_timeout_clears_waiting_flag():
    state = ClientState()
    state.handle_message({
        "type": "request_ok",
        "payload": {"status": "waiting"},
    })
    state.handle_message({"type": "matchmaking_timeout", "payload": {}})
    assert state.matchmaking_waiting is False
    assert state.last_error["code"] == "MATCHMAKING_TIMEOUT"
    assert "No suitable opponent found" in state.last_error["message"]
