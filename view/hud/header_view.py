import cv2

from config.constants import (
    EXIT_BUTTON_BG,
    EXIT_BUTTON_TEXT,
    HEADER_BG_COLOR,
)


class HeaderView:
    """
    Top area of the screen.
    Shows optional remote-session status (room type / spectator)
    and an Exit Game button on the right.
    """

    FONT = cv2.FONT_HERSHEY_SIMPLEX

    def render(self, canvas, rect, snapshot, exit_button_rect=None):
        cv2.rectangle(
            canvas,
            (rect.x, rect.y),
            (rect.x + rect.width, rect.y + rect.height),
            HEADER_BG_COLOR,
            thickness=-1,
        )
        line = getattr(snapshot, "hud_line", None)
        if line:
            cv2.putText(
                canvas,
                str(line),
                (rect.x + 16, rect.y + max(22, rect.height // 2 + 6)),
                self.FONT,
                0.55,
                (220, 220, 220),
                1,
                cv2.LINE_AA,
            )

        if exit_button_rect is not None:
            self._draw_exit_button(canvas, exit_button_rect)

    def _draw_exit_button(self, canvas, rect):
        cv2.rectangle(
            canvas,
            (rect.x, rect.y),
            (rect.x + rect.width - 1, rect.y + rect.height - 1),
            EXIT_BUTTON_BG,
            thickness=-1,
        )
        label = "Exit Game"
        (tw, th), _ = cv2.getTextSize(label, self.FONT, 0.5, 1)
        tx = rect.x + max(0, (rect.width - tw) // 2)
        ty = rect.y + max(th, (rect.height + th) // 2) - 2
        cv2.putText(
            canvas,
            label,
            (tx, ty),
            self.FONT,
            0.5,
            EXIT_BUTTON_TEXT,
            1,
            cv2.LINE_AA,
        )
