import cv2

from config.constants import HEADER_BG_COLOR


class HeaderView:
    """
    Top area of the screen.
    Currently renders a plain dark bar.
    """

    def render(self, canvas, rect, snapshot):
        cv2.rectangle(
            canvas,
            (rect.x, rect.y),
            (rect.x + rect.width, rect.y + rect.height),
            HEADER_BG_COLOR,
            thickness=-1,
        )
