import os

import cv2

from config.constants import TICK_MS
from view.frame_clock import FrameClock
from view.game_runner import get_work_area
from view.input.input_handler import InputHandler


class RemoteGameRunner:
    """
    OpenCV loop driven by ClientState snapshots from the server.
    """

    def __init__(self, session, controller, renderer, window_name=None, frame_clock=None):
        self._session = session
        self._renderer = renderer
        self._input_handler = InputHandler(controller)
        self._frame_clock = frame_clock or FrameClock()
        self._window_name = window_name or f"KFChess Remote {os.getpid()}"
        self._running = False

    def run(self):
        self._create_window()
        self._running = True
        try:
            self._run_loop()
        finally:
            self._running = False
            cv2.destroyWindow(self._window_name)

    def _run_loop(self):
        while self._running:
            self._session.pump()
            self._frame_clock.tick(TICK_MS)

            snapshot = self._session.state.create_snapshot()
            frame = self._renderer.render(snapshot, self._frame_clock.now_ms())
            if frame is not None:
                cv2.imshow(self._window_name, frame)

            key = cv2.waitKey(TICK_MS)
            if not self._input_handler.handle(key):
                self._running = False
                continue

            if snapshot.game_over:
                cv2.waitKey(0)
                self._running = False

    def _create_window(self):
        work_width, work_height = get_work_area()
        cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self._window_name, work_width, work_height)
        cv2.moveWindow(self._window_name, 0, 0)
        cv2.setMouseCallback(self._window_name, self._on_mouse)

    def _on_mouse(self, event, x, y, flags, param):
        self._input_handler.handle_mouse(x, y, event)
