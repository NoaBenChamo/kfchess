from view.rendering.window_composer import WindowComposer


class WindowRenderer:
    """
    Renders one complete game window frame.

    Rendering order:
        Header
        Left player panel
        Board
        Right player panel
        Footer
    """

    def __init__(
        self,
        layout,
        header_view,
        left_player_view,
        board_view,
        right_player_view,
        footer_view,
        window_composer=None,
    ):
        self._layout = layout
        self._header_view = header_view
        self._left_player_view = left_player_view
        self._board_view = board_view
        self._right_player_view = right_player_view
        self._footer_view = footer_view
        self._composer = window_composer or WindowComposer(
            layout.total_width,
            layout.total_height,
        )

    def render(self, snapshot, animation_time_ms):
        """
        Renders one complete game frame.

        Returns:
            NumPy BGRA array for the whole window.
        """
        canvas = self._composer.create_canvas()

        self._header_view.render(
            canvas,
            self._layout.header_rect,
            snapshot,
        )

        self._left_player_view.render(
            canvas,
            self._layout.left_player_rect,
            snapshot,
        )

        self._board_view.render(
            canvas,
            self._layout.board_canvas_rect,
            snapshot,
            animation_time_ms,
        )

        self._right_player_view.render(
            canvas,
            self._layout.right_player_rect,
            snapshot,
        )

        self._footer_view.render(
            canvas,
            self._layout.footer_rect,
            snapshot,
        )

        return canvas
