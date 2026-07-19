import cv2
import numpy as np


class HeaderView:
    """
    Top area of the screen.
    Currently renders a plain dark bar.
    Reserved for future game title or status information.
    """

    def render(self, canvas, rect):
        x, y, w, h = rect
        cv2.rectangle(canvas, (x, y), (x + w, y + h), (30, 30, 30, 255), thickness=-1)
