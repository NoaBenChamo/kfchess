import cv2


class PlayerView:
    """
    Side panel for one player.
    Currently renders a plain dark bar.
    Reserved for future player name, captured pieces, and move history.
    Player data and move history are not yet implemented.
    """

    def render(self, canvas, rect):
        x, y, w, h = rect
        cv2.rectangle(canvas, (x, y), (x + w, y + h), (20, 20, 20, 255), thickness=-1)
