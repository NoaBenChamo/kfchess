import cv2
from config.constants import FOOTER_BG_COLOR


class FooterView:
    """
    Bottom area of the screen.
    Currently renders a plain dark bar.
    Reserved for future status information.
    """

    def render(self, canvas, rect):
        cv2.rectangle(
            canvas,
            (rect.x, rect.y),
            (rect.x + rect.width, rect.y + rect.height),
            FOOTER_BG_COLOR,
            thickness=-1,
        )
