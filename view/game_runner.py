import ctypes

import cv2

from config.constants import TICK_MS, WINDOW_NAME
from view.input.input_handler import InputHandler


def get_work_area():
    """
    Returns the usable Windows desktop size, excluding the taskbar.

    Returns:
        tuple[int, int]: Work-area width and height.
    """

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
        raise RuntimeError("Could not read the Windows work area")

    width = rect.right - rect.left
    height = rect.bottom - rect.top

    return width, height


class GameRunner:
    """
    Runs the main game loop.

    Responsible for:
        - advancing the game clock
        - creating snapshots
        - rendering frames
        - forwarding keyboard and mouse input
        - opening and closing the OpenCV window

    GameRunner does not contain game rules or drawing logic.
    """

    def __init__(self, engine, controller, renderer):
        self._engine = engine
        self._renderer = renderer
        self._input_handler = InputHandler(controller)

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
            cv2.destroyAllWindows()

    def _run_loop(self):
        while self._running:
            self._engine.tick(TICK_MS)

            snapshot = self._engine.create_snapshot()
            frame = self._renderer.render(snapshot)

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

        cv2.namedWindow(
            WINDOW_NAME,
            cv2.WINDOW_NORMAL,
        )

        cv2.resizeWindow(
            WINDOW_NAME,
            work_width,
            work_height,
        )

        cv2.moveWindow(
            WINDOW_NAME,
            0,
            0,
        )

        cv2.setMouseCallback(
            WINDOW_NAME,
            self._on_mouse,
        )

    def _show_frame(self, frame):
        """
        Displays the frame returned by Renderer.

        Supports either:
            - a NumPy image
            - an Img object containing an ``img`` attribute
        """
        if frame is None:
            return

        image = frame.img if hasattr(frame, "img") else frame

        if image is None:
            return

        cv2.imshow(
            WINDOW_NAME,
            image,
        )

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