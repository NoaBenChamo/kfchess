import cv2

from config.constants import (
    PLAYER_BG_COLOR,
    PLAYER_TITLE_COLOR,
    PLAYER_MOVE_COLOR,
    PLAYER_PADDING,
    PLAYER_TITLE_FONT_SCALE,
    PLAYER_MOVE_FONT_SCALE,
    PLAYER_SCORE_FONT_SCALE,
    PLAYER_SCORE_LINE_HEIGHT,
    PLAYER_SCORE_COLOR,
    PLAYER_TABLE_BORDER_COLOR,
    PLAYER_TABLE_HEADER_BG,
    PLAYER_TABLE_HEADER_COLOR,
    PLAYER_TABLE_TIME_COLOR,
    PLAYER_TABLE_HEADER_HEIGHT,
    PLAYER_TABLE_ROW_HEIGHT,
)


def format_move_time(time_ms):
    """Formats game time as MM:SS.mmm for the player panel."""
    if time_ms is None:
        return ""

    total_ms = max(0, int(time_ms))
    minutes, remainder_ms = divmod(total_ms, 60_000)
    seconds, millis = divmod(remainder_ms, 1000)

    return f"{minutes:02d}:{seconds:02d}.{millis:03d}"


def format_move_notation(record):
    """Formats a move record as compact destination notation for the MOVE column."""
    cols = "abcdefgh"
    rows = "87654321"
    target = cols[record.target.col] + rows[record.target.row]

    if record.move_type == "jump":
        return f"JUMP {target}"

    if record.piece_type == "P":
        return target

    return f"{record.piece_type}{target}"


class PlayerView:
    """
    Side panel for one player.
    Renders player title, score, and a TIME / MOVE history table.
    """

    FONT = cv2.FONT_HERSHEY_SIMPLEX
    HEADER_FONT_SCALE = 0.42
    CELL_FONT_SCALE = 0.40

    def __init__(self, side):
        if side not in ("white", "black"):
            raise ValueError("side must be 'white' or 'black'")
        self._side = side
        self._title = "Player 1" if side == "white" else "Player 2"

    def render(self, canvas, rect, snapshot):
        moves, score = self._side_data(snapshot)

        panel_x = rect.x
        panel_y = rect.y
        panel_width = rect.width
        panel_height = rect.height

        cv2.rectangle(
            canvas,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            PLAYER_BG_COLOR,
            thickness=-1,
        )

        content_x = panel_x + PLAYER_PADDING
        content_width = panel_width - 2 * PLAYER_PADDING

        title_y = panel_y + PLAYER_PADDING + 14
        title = self._display_title(snapshot)
        cv2.putText(
            canvas,
            title,
            (content_x, title_y),
            self.FONT,
            PLAYER_TITLE_FONT_SCALE,
            PLAYER_TITLE_COLOR,
            1,
            cv2.LINE_AA,
        )

        next_y = title_y + PLAYER_SCORE_LINE_HEIGHT
        rating = self._display_rating(snapshot)
        if rating is not None:
            cv2.putText(
                canvas,
                f"ELO: {rating}",
                (content_x, next_y),
                self.FONT,
                PLAYER_SCORE_FONT_SCALE,
                PLAYER_TITLE_COLOR,
                1,
                cv2.LINE_AA,
            )
            next_y += PLAYER_SCORE_LINE_HEIGHT

        score_y = next_y
        cv2.putText(
            canvas,
            f"Score: {score}",
            (content_x, score_y),
            self.FONT,
            PLAYER_SCORE_FONT_SCALE,
            PLAYER_SCORE_COLOR,
            1,
            cv2.LINE_AA,
        )

        table_y = score_y + PLAYER_PADDING + 6
        table_height = panel_y + panel_height - PLAYER_PADDING - table_y

        if table_height > PLAYER_TABLE_HEADER_HEIGHT + PLAYER_TABLE_ROW_HEIGHT:
            self._draw_history_table(
                canvas,
                content_x,
                table_y,
                content_width,
                table_height,
                moves,
            )

    def _side_data(self, snapshot):
        if self._side == "white":
            return snapshot.white_moves, snapshot.white_score

        return snapshot.black_moves, snapshot.black_score

    def _display_title(self, snapshot):
        if self._side == "white":
            name = getattr(snapshot, "white_username", None)
        else:
            name = getattr(snapshot, "black_username", None)
        if name:
            return str(name)
        return self._title

    def _display_rating(self, snapshot):
        if self._side == "white":
            rating = getattr(snapshot, "white_rating", None)
        else:
            rating = getattr(snapshot, "black_rating", None)
        if rating is None:
            return None
        return rating

    def _draw_history_table(self, canvas, x, y, width, height, moves):
        cv2.rectangle(
            canvas,
            (x, y),
            (x + width, y + height),
            PLAYER_TABLE_BORDER_COLOR,
            thickness=1,
        )

        header_bottom = y + PLAYER_TABLE_HEADER_HEIGHT
        cv2.rectangle(
            canvas,
            (x + 1, y + 1),
            (x + width - 1, header_bottom),
            PLAYER_TABLE_HEADER_BG,
            thickness=-1,
        )

        col_width = width // 2
        divider_x = x + col_width

        cv2.line(
            canvas,
            (divider_x, y),
            (divider_x, y + height),
            PLAYER_TABLE_BORDER_COLOR,
            1,
        )

        cv2.line(
            canvas,
            (x, header_bottom),
            (x + width, header_bottom),
            PLAYER_TABLE_BORDER_COLOR,
            1,
        )

        for label, column_x in (("TIME", x), ("MOVE", x + col_width)):
            self._draw_centered_text(
                canvas,
                label,
                column_x,
                y,
                col_width,
                PLAYER_TABLE_HEADER_HEIGHT,
                self.HEADER_FONT_SCALE,
                PLAYER_TABLE_HEADER_COLOR,
            )

        rows_top = header_bottom
        available_height = height - PLAYER_TABLE_HEADER_HEIGHT
        max_rows = max(0, available_height // PLAYER_TABLE_ROW_HEIGHT)
        visible_moves = moves[-max_rows:] if max_rows < len(moves) else moves

        for row_index, record in enumerate(visible_moves):
            row_y = rows_top + row_index * PLAYER_TABLE_ROW_HEIGHT
            if row_y + PLAYER_TABLE_ROW_HEIGHT > y + height:
                break

            self._draw_table_row(
                canvas,
                x,
                row_y,
                col_width,
                record,
            )

    def _draw_table_row(self, canvas, x, row_y, col_width, record):
        self._draw_centered_text(
            canvas,
            format_move_time(record.time_ms),
            x,
            row_y,
            col_width,
            PLAYER_TABLE_ROW_HEIGHT,
            self.CELL_FONT_SCALE,
            PLAYER_TABLE_TIME_COLOR,
        )
        self._draw_centered_text(
            canvas,
            format_move_notation(record),
            x + col_width,
            row_y,
            col_width,
            PLAYER_TABLE_ROW_HEIGHT,
            self.CELL_FONT_SCALE,
            PLAYER_MOVE_COLOR,
        )

    @staticmethod
    def _draw_centered_text(
        canvas,
        text,
        x,
        y,
        width,
        height,
        font_scale,
        color,
    ):
        if not text:
            return

        text_size, _ = cv2.getTextSize(
            text,
            PlayerView.FONT,
            font_scale,
            1,
        )

        text_x = x + max(0, (width - text_size[0]) // 2)
        text_y = y + (height + text_size[1]) // 2

        cv2.putText(
            canvas,
            text,
            (text_x, text_y),
            PlayerView.FONT,
            font_scale,
            color,
            1,
            cv2.LINE_AA,
        )
