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
    When the loop ends (Exit Game, game over acknowledge, or connection lost),
    the caller (remote_ui) returns to the startup/lobby screen.
    """

    def __init__(
        self,
        session,
        controller,
        renderer,
        window_name=None,
        frame_clock=None,
        exit_button_rect=None,
    ):
        self._session = session
        self._renderer = renderer
        self._input_handler = InputHandler(controller)
        self._frame_clock = frame_clock or FrameClock()
        self._window_name = window_name or WINDOW_NAME
        self._exit_button_rect = exit_button_rect

        self._running = False
        self._return_to_lobby = False

    @property
    def return_to_lobby(self):
        """True when the runner ended in a way that should reopen StartupWindow."""
        return self._return_to_lobby

    def run(self):
        """
        Opens the game window and runs the main loop.
        """
        self._create_window()
        self._running = True
        self._return_to_lobby = False

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
                self._leave_and_return_to_lobby()
                continue

            if getattr(self._session, "connection_lost", False):
                self._return_to_lobby = True
                self._running = False
                continue

            if snapshot.game_over:
                self._wait_for_exit()
                self._return_to_lobby = True
                self._running = False

    def _leave_and_return_to_lobby(self):
        leave = getattr(self._session, "request_leave", None)
        if callable(leave):
            leave()
        self._return_to_lobby = True
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
        Keeps the final game-over frame visible until a key is pressed
        or the Exit Game button is clicked.
        """
        while True:
            key = cv2.waitKey(50)
            if key != -1:
                return
            # Allow Exit Game during the acknowledge pause.
            # Mouse clicks are handled via the callback setting a flag.
            if getattr(self, "_exit_clicked_during_wait", False):
                self._exit_clicked_during_wait = False
                return

    def _on_mouse(self, event, x, y, flags, param):
        """
        Forwards OpenCV mouse events to InputHandler, except Exit Game.
        """
        if event == cv2.EVENT_LBUTTONDOWN and self._hit_exit(x, y):
            if self._session.game_over:
                self._exit_clicked_during_wait = True
                return
            self._leave_and_return_to_lobby()
            return

        self._input_handler.handle_mouse(
            x,
            y,
            event,
        )

    def _hit_exit(self, x, y):
        rect = self._exit_button_rect
        if rect is None:
            return False
        return rect.contains(x, y)
