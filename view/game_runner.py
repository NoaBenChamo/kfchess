import cv2

from config.constants import TICK_MS, WINDOW_NAME
from view.frame_clock import FrameClock
from view.input.input_handler import InputHandler

DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 900


def get_work_area():
    """
    Returns the usable desktop size, excluding the taskbar on Windows.

    Falls back to a reasonable default when the OS API is unavailable.

    Returns:
        tuple[int, int]: Work-area width and height.
    """
    try:
        import ctypes

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", ctypes.c_long),
                ("top", ctypes.c_long),
                ("right", ctypes.c_long),
                ("bottom", ctypes.c_long),
            ]

        rect = RECT()

        success = ctypes.windll.user32.SystemParametersInfoW(
            48,
            0,
            ctypes.byref(rect),
            0,
        )

        if not success:
            return DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT

        width = rect.right - rect.left
        height = rect.bottom - rect.top

        if width <= 0 or height <= 0:
            return DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT

        return width, height

    except (AttributeError, OSError):
        return DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT


class GameRunner:
    """
    Runs the main game loop.

    Responsible for:
        - advancing the play session
        - creating snapshots
        - rendering frames
        - forwarding keyboard and mouse input
        - opening and closing the OpenCV window

    GameRunner does not contain game rules, networking, or drawing logic.
    """

    def __init__(self, session, controller, renderer, window_name=None, frame_clock=None):
        self._session = session
        self._renderer = renderer
        self._input_handler = InputHandler(controller)
        self._frame_clock = frame_clock or FrameClock()
        self._window_name = window_name or WINDOW_NAME

        self._running = False

    def run(self):
        """
        Opens the game window and runs the main loop.
        """
        self._create_window()
        self._running = True

        try:
            self._run_loop()
        finally:
            self._running = False
            cv2.destroyWindow(self._window_name)

    def _run_loop(self):
        while self._running:
            self._session.pump(TICK_MS)
            self._frame_clock.tick(TICK_MS)

            snapshot = self._session.create_snapshot()
            frame = self._renderer.render(snapshot, self._animation_time_ms())

            self._show_frame(frame)

            key = cv2.waitKey(TICK_MS)

            if not self._input_handler.handle(key):
                self._running = False
                continue

            if snapshot.game_over:
                self._wait_for_exit()
                self._running = False

    def _create_window(self):
        work_width, work_height = get_work_area()
        cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self._window_name, work_width, work_height)
        cv2.moveWindow(self._window_name, 0, 0)
        cv2.setMouseCallback(self._window_name, self._on_mouse)

    def _animation_time_ms(self):
        return self._frame_clock.now_ms()

    def _show_frame(self, frame):
        """
        Displays the frame returned by Renderer.
        """
        if frame is None:
            return
        cv2.imshow(self._window_name, frame)

    def _wait_for_exit(self):
        """
        Keeps the final game-over frame visible until a key is pressed.
        """
        cv2.waitKey(0)

    def _on_mouse(self, event, x, y, flags, param):
        """
        Forwards OpenCV mouse events to InputHandler.
        """
        self._input_handler.handle_mouse(
            x,
            y,
            event,
        )
