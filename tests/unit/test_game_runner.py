from snapshots.game_snapshot import GameSnapshot

from view.game_runner import GameRunner


class _FakeRenderer:
    def __init__(self):
        self.frames = []

    def render(self, snapshot, animation_time_ms):
        del animation_time_ms
        self.frames.append(snapshot)
        return None


class _FakeSession:
    def __init__(self, snapshots):
        self._snapshots = list(snapshots)
        self.pump_calls = []

    def pump(self, elapsed_ms):
        self.pump_calls.append(elapsed_ms)

    def create_snapshot(self):
        if len(self._snapshots) == 1:
            return self._snapshots[0]
        return self._snapshots.pop(0)

    def get_selected(self):
        return None

    def select(self, position):
        del position

    def clear_selection(self):
        pass

    def request_move_to(self, target):
        del target

    def request_jump_to(self, target):
        del target

    @property
    def game_over(self):
        return self.create_snapshot().game_over


class _FakeController:
    def click(self, x, y):
        del x, y

    def jump(self, x, y):
        del x, y


def _snapshot(game_over=False):
    return GameSnapshot(
        board_width=8,
        board_height=8,
        pieces=[],
        selected_cell=None,
        game_over=game_over,
    )


def test_game_runner_pumps_session_each_frame(monkeypatch):
    session = _FakeSession([_snapshot(), _snapshot(game_over=True)])
    renderer = _FakeRenderer()
    runner = GameRunner(session, _FakeController(), renderer, window_name="test-runner")

    monkeypatch.setattr("view.game_runner.cv2.namedWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.resizeWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.moveWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.setMouseCallback", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.destroyWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.waitKey", lambda *args, **kwargs: -1)

    runner.run()

    assert len(session.pump_calls) >= 1
    assert len(renderer.frames) >= 1


def test_game_runner_stops_when_session_snapshot_reports_game_over(monkeypatch):
    session = _FakeSession([_snapshot(game_over=True)])
    renderer = _FakeRenderer()
    runner = GameRunner(session, _FakeController(), renderer, window_name="test-runner-over")
    wait_calls = []

    monkeypatch.setattr("view.game_runner.cv2.namedWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.resizeWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.moveWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.setMouseCallback", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.destroyWindow", lambda *args, **kwargs: None)

    def fake_wait_key(delay):
        wait_calls.append(delay)
        return -1

    monkeypatch.setattr("view.game_runner.cv2.waitKey", fake_wait_key)

    runner.run()

    assert 0 in wait_calls
