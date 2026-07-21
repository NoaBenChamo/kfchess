from model.position import Position

from client.client_state import ClientState
from client.remote_session import RemoteSession


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


def _make_session_with_snapshot():
    session = RemoteSession("ws://unused")
    session.state.handle_message({
        "type": "state_snapshot",
        "payload": _sample_snapshot(),
    })
    return session


def test_remote_session_select_stores_local_selection():
    session = _make_session_with_snapshot()

    session.select(Position(6, 4))

    assert session.get_selected() == Position(6, 4)


def test_remote_session_select_ignores_empty_square():
    session = _make_session_with_snapshot()

    session.select(Position(0, 0))

    assert session.get_selected() is None


def test_remote_session_request_move_to_queues_command_without_mutating_board():
    session = _make_session_with_snapshot()
    session.select(Position(6, 4))

    session.request_move_to(Position(4, 4))

    assert session.get_selected() is None
    assert not session._outgoing.empty()
    kind, command = session._outgoing.get_nowait()
    assert kind == "move"
    assert command == "WPe2e4"
    assert session.state.snapshot_dict["pieces"][0]["row"] == 6


def test_remote_session_pump_applies_incoming_messages():
    session = RemoteSession("ws://unused")
    session._incoming.put({
        "type": "state_snapshot",
        "payload": _sample_snapshot(3),
    })

    session.pump(16)

    assert session.state.sequence == 3
    assert session.create_snapshot().board_width == 8


def test_remote_session_game_over_reflects_snapshot():
    session = _make_session_with_snapshot()
    assert not session.game_over

    session.state.handle_message({
        "type": "state_snapshot",
        "payload": {**_sample_snapshot(1), "game_over": True},
    })

    assert session.game_over
