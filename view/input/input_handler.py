import cv2


class InputHandler:
    """
    Converts raw keyboard and mouse input into controller actions.

    InputHandler does not contain game rules.
    It only translates input events into controller commands.
    """

    def __init__(self, controller):
        self._controller = controller

    def handle(self, key):
        """
        Handles a keyboard event.

        Returns:
            False when the game should stop.
            True otherwise.
        """
        if key == ord("q"):
            return False

        return True

    def handle_mouse(self, x, y, event):
        """
        Handles a mouse event in full-window pixel coordinates.
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            self._controller.click(x, y)

        elif event == cv2.EVENT_RBUTTONDOWN:
            self._controller.jump(x, y)