import cv2
from config.constants import (
    PLAYER_BG_COLOR, PLAYER_TITLE_COLOR, PLAYER_MOVE_COLOR,
    PLAYER_DIVIDER_COLOR, PLAYER_PADDING,
    PLAYER_TITLE_FONT_SCALE, PLAYER_MOVE_FONT_SCALE, PLAYER_LINE_HEIGHT,
)


class PlayerView:
    """
    Side panel for one player.
    Renders the player's move history.
    The same class is used for both left (white) and right (black) panels.
    """

    FONT = cv2.FONT_HERSHEY_SIMPLEX

    def __init__(self, title):
        self._title = title

    def render(self, canvas, rect, moves):
        x = rect.x
        y = rect.y
        w = rect.width
        h = rect.height

        cv2.rectangle(
            canvas, (x, y), (x + w, y + h), PLAYER_BG_COLOR, thickness=-1
        )

        cv2.putText(
            canvas, self._title,
            (x + PLAYER_PADDING, y + PLAYER_PADDING + 14),
            self.FONT, PLAYER_TITLE_FONT_SCALE, PLAYER_TITLE_COLOR, 1, cv2.LINE_AA,
        )

        title_bottom = y + PLAYER_PADDING + 22
        cv2.line(
            canvas,
            (x + PLAYER_PADDING, title_bottom),
            (x + w - PLAYER_PADDING, title_bottom),
            PLAYER_DIVIDER_COLOR, 1,
        )

        list_top = title_bottom + PLAYER_PADDING
        available_h = h - (list_top - y) - PLAYER_PADDING
        max_visible = max(0, available_h // PLAYER_LINE_HEIGHT)

        visible = moves[-max_visible:] if max_visible < len(moves) else moves

        for i, record in enumerate(visible):
            move_y = list_top + i * PLAYER_LINE_HEIGHT + 12
            if move_y > y + h - PLAYER_PADDING:
                break
            cv2.putText(
                canvas,
                f"{len(moves) - len(visible) + i + 1}. {record}",
                (x + PLAYER_PADDING, move_y),
                self.FONT, PLAYER_MOVE_FONT_SCALE, PLAYER_MOVE_COLOR, 1, cv2.LINE_AA,
            )
