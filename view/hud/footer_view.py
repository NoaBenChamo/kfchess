import cv2

from config.constants import FOOTER_BG_COLOR


class FooterView:
    """
    Bottom area of the screen.
    Currently renders a plain dark bar.
    """

    def render(self, canvas, rect, snapshot):
        cv2.rectangle(
            canvas,
            (rect.x, rect.y),
            (rect.x + rect.width, rect.y + rect.height),
            FOOTER_BG_COLOR,
            thickness=-1,
        )
