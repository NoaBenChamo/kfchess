import cv2
#listen to the input from the users and convert it to a fit action
class InputHandler:

    def __init__(self, controller):
        self._controller = controller

    def handle(self, event):
        if event == ord('q'):
            return False
        return True

    def handle_mouse(self, x, y, event):
        if event == cv2.EVENT_LBUTTONDOWN:
            self._controller.click(x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._controller.jump(x, y)