from model.board import Board
from model.piece import Piece
from model.position import Position
from snapshots.game_snapshot import GameSnapshot
from snapshots.piece_snapshot import PieceSnapshot

from client.remote_session import RemoteSession
from engine.game_engine import GameEngine
from input.controller import Controller
from session.local_session import LocalSession


class _FakeMapper:
    def __init__(self, mapping):
        self._mapping = mapping

    def to_position(self, x, y):
        return self._mapping.get((x, y))


def _sample_snapshot_dict():
    return {
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
    }


def _pawn_snapshot():
    return GameSnapshot(
        board_width=8,
        board_height=8,
        pieces=[
            PieceSnapshot("w", "P", Position(6, 4), "idle"),
        ],
        selected_cell=None,
        game_over=False,
    )


class _RecordingSession:
    def __init__(self, snapshot):
        self._snapshot = snapshot
        self.selected = None
        self.moves = []
        self.jumps = []

    def pump(self, elapsed_ms):
        del elapsed_ms

    def create_snapshot(self):
        return GameSnapshot(
            board_width=self._snapshot.board_width,
            board_height=self._snapshot.board_height,
            pieces=list(self._snapshot.pieces),
            selected_cell=self.selected,
            game_over=self._snapshot.game_over,
        )

    def get_selected(self):
        return self.selected

    def select(self, position):
        if self._piece_at(position) is None:
            return
        self.selected = position

    def clear_selection(self):
        self.selected = None

    def request_move_to(self, target):
        self.moves.append(target)

    def request_jump_to(self, target):
        self.jumps.append(target)

    @property
    def game_over(self):
        return self._snapshot.game_over

    def _piece_at(self, position):
        for piece in self._snapshot.pieces:
            if piece.position == position:
                return piece
        return None


def test_controller_with_remote_session_sends_move_command_after_two_clicks():
    session = RemoteSession("ws://unused", username="Alice")
    session.state.handle_message({
        "type": "identity_assigned",
        "payload": {"username": "Alice", "color": "w", "game_id": "default"},
    })
    session.state.handle_message({
        "type": "state_snapshot",
        "payload": _sample_snapshot_dict(),
    })

    mapper = _FakeMapper({
        (10, 10): Position(6, 4),  # e2
        (20, 20): Position(4, 4),  # e4
    })
    controller = Controller(session, mapper)

    controller.click(10, 10)
    assert session.get_selected() == Position(6, 4)

    controller.click(20, 20)
    kind, command = session._outgoing.get_nowait()
    assert kind == "move"
    assert command == "WPe2e4"
    assert session.get_selected() is None


def test_controller_parity_click_sequence_records_move_request():
    mapper = _FakeMapper({
        (10, 10): Position(6, 4),
        (20, 20): Position(4, 4),
    })
    snapshot = _pawn_snapshot()

    local_engine = GameEngine(Board([[None] * 8 for _ in range(8)]))
    local_engine._board.set(Position(6, 4), Piece("w", "P"))
    local_session = LocalSession(local_engine)
    local_controller = Controller(local_session, mapper)

    remote_session = _RecordingSession(snapshot)
    remote_controller = Controller(remote_session, mapper)

    local_controller.click(10, 10)
    remote_controller.click(10, 10)
    assert local_session.get_selected() == Position(6, 4)
    assert remote_session.selected == Position(6, 4)

    local_controller.click(20, 20)
    remote_controller.click(20, 20)
    assert local_session.get_selected() is None
    assert remote_session.moves == [Position(4, 4)]


def test_controller_with_recording_session_records_jump():
    mapper = _FakeMapper({(10, 10): Position(0, 0)})
    session = _RecordingSession(_pawn_snapshot())
    controller = Controller(session, mapper)

    controller.jump(10, 10)

    assert session.jumps == [Position(0, 0)]
