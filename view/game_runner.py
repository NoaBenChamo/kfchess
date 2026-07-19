import ctypes
import cv2
from config.constants import TICK_MS, WINDOW_NAME
from view.input.input_handler import InputHandler


def get_work_area():
    """
    Returns (width, height) of the screen work area (excluding the taskbar).
    Uses the Windows API via ctypes.
    """
    class RECT(ctypes.Structure):
        _fields_ = [
            ("left",   ctypes.c_long),
            ("top",    ctypes.c_long),
            ("right",  ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    rect = RECT()
    ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
    return rect.right - rect.left, rect.bottom - rect.top


class GameRunner:

    def __init__(self, engine, controller, renderer):
        self._engine = engine
        self._controller = controller
        self._renderer = renderer
        self._input_handler = InputHandler(controller)

    def run(self):
        work_w, work_h = get_work_area()

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, work_w, work_h)
        cv2.moveWindow(WINDOW_NAME, 0, 0)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)

        while True:
            self._engine.tick(TICK_MS)
            snapshot = self._engine.create_snapshot()
            self._renderer.render(snapshot)

            key = cv2.waitKey(TICK_MS)
            if not self._input_handler.handle(key):
                break
            if snapshot.game_over:
                cv2.waitKey(0)
                break

        cv2.destroyAllWindows()

    def _on_mouse(self, event, x, y, flags, param):
        self._input_handler.handle_mouse(x, y, event)
