import cv2


class InputHandler:

    def __init__(self, controller):
        self._controller = controller

    def handle(self, event):
        if event == ord('q'):
            return False
        return True

    def handle_mouse(self, x, y, flags):
        if flags == cv2.EVENT_LBUTTONDOWN:
            self._controller.click(x, y)
        elif flags == cv2.EVENT_RBUTTONDOWN:
            self._controller.jump(x, y)
