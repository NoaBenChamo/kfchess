import cv2
from view.input_handler import InputHandler

TICK_MS = 16
WINDOW_NAME = "KFChess"


class GameRunner:

    def __init__(self, engine, controller, renderer):
        self._engine = engine
        self._controller = controller
        self._renderer = renderer
        self._input_handler = InputHandler(controller)

    def run(self):
        cv2.namedWindow(WINDOW_NAME)
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
