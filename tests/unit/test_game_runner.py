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

    def fake_wait_key(delay):
        # Acknowledge game-over pause so the runner can exit.
        if delay == 50:
            return ord(" ")
        return -1

    monkeypatch.setattr("view.game_runner.cv2.waitKey", fake_wait_key)

    runner.run()

    assert len(session.pump_calls) >= 1
    assert len(renderer.frames) >= 1
    assert runner.return_to_lobby is True


def test_game_runner_stops_on_connection_lost(monkeypatch):
    class _LostSession(_FakeSession):
        connection_lost = False

        def pump(self, elapsed_ms):
            super().pump(elapsed_ms)
            self.connection_lost = True

    session = _LostSession([_snapshot()])
    renderer = _FakeRenderer()
    runner = GameRunner(
        session, _FakeController(), renderer, window_name="test-runner-lost"
    )

    monkeypatch.setattr("view.game_runner.cv2.namedWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.resizeWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.moveWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.setMouseCallback", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.destroyWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.waitKey", lambda *args, **kwargs: -1)

    runner.run()
    assert session.connection_lost is True
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
        # Acknowledge game-over pause (50ms poll) with a keypress.
        if delay == 50:
            return ord(" ")
        return -1

    monkeypatch.setattr("view.game_runner.cv2.waitKey", fake_wait_key)

    runner.run()

    assert 50 in wait_calls
    assert runner.return_to_lobby is True


def test_game_runner_exit_button_requests_leave_and_returns_to_lobby(monkeypatch):
    from input.screen_rect import ScreenRect

    class _LeaveSession(_FakeSession):
        def __init__(self):
            super().__init__([_snapshot()])
            self.leave_calls = 0

        def request_leave(self):
            self.leave_calls += 1

    session = _LeaveSession()
    renderer = _FakeRenderer()
    exit_rect = ScreenRect(100, 10, 110, 36)
    mouse_cb = {}

    def capture_mouse(name, callback):
        mouse_cb["fn"] = callback

    runner = GameRunner(
        session,
        _FakeController(),
        renderer,
        window_name="test-runner-exit",
        exit_button_rect=exit_rect,
    )

    monkeypatch.setattr("view.game_runner.cv2.namedWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.resizeWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.moveWindow", lambda *args, **kwargs: None)
    monkeypatch.setattr("view.game_runner.cv2.setMouseCallback", capture_mouse)
    monkeypatch.setattr("view.game_runner.cv2.destroyWindow", lambda *args, **kwargs: None)

    frames = {"n": 0}

    def fake_wait_key(delay):
        del delay
        frames["n"] += 1
        if frames["n"] == 1 and "fn" in mouse_cb:
            import cv2

            mouse_cb["fn"](cv2.EVENT_LBUTTONDOWN, exit_rect.x + 5, exit_rect.y + 5, 0, None)
        return -1

    monkeypatch.setattr("view.game_runner.cv2.waitKey", fake_wait_key)

    runner.run()

    assert session.leave_calls == 1
    assert runner.return_to_lobby is True
