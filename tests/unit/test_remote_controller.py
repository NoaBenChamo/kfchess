from model.position import Position

from client.client_state import ClientState
from client.remote_controller import RemoteController


class _FakeMapper:
    def __init__(self, mapping):
        self._mapping = mapping

    def to_position(self, x, y):
        return self._mapping.get((x, y))


class _FakeSession:
    def __init__(self):
        self.state = ClientState()
        self.sent = []

    def send_move(self, command):
        self.sent.append(command)


def test_remote_controller_sends_move_command_after_two_clicks():
    session = _FakeSession()
    session.state.handle_message({
        "type": "state_snapshot",
        "payload": {
            "sequence": 0,
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
        },
    })

    mapper = _FakeMapper({
        (10, 10): Position(6, 4),  # e2
        (20, 20): Position(4, 4),  # e4
    })
    controller = RemoteController(session, mapper)

    controller.click(10, 10)
    assert session.state.selected == Position(6, 4)

    controller.click(20, 20)
    assert session.sent == ["WPe2e4"]
    assert session.state.selected is None
