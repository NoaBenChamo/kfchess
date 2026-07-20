class BoardView:
    """
    Coordinates the rendering of the board region.

    Rendering order:
        1. Static board
        2. Selected-cell highlight
        3. Chess pieces
        4. Rest/cooldown overlays
        5. Game over overlay
    """

    def __init__(
        self,
        board_renderer,
        highlight_renderer,
        piece_renderer,
        rest_overlay_renderer,
        game_over_renderer,
    ):
        self._board_renderer = board_renderer
        self._highlight_renderer = highlight_renderer
        self._piece_renderer = piece_renderer
        self._rest_overlay_renderer = rest_overlay_renderer
        self._game_over_renderer = game_over_renderer

    def render(self, canvas, rect, snapshot, animation_time_ms):
        """
        Renders the board into the given window region.
        """
        local = self._board_renderer.create_canvas(
            canvas_width=rect.width,
            canvas_height=rect.height,
        )

        self._highlight_renderer.render(
            local,
            snapshot.selected_cell,
        )

        self._piece_renderer.render(
            local,
            snapshot.pieces,
            animation_time_ms,
        )

        self._rest_overlay_renderer.render(
            local,
            snapshot.pieces,
        )

        if snapshot.game_over:
            self._game_over_renderer.render(local)

        self._paste(canvas, local.img, rect)

    @staticmethod
    def _paste(window, image, rect):
        if image is None:
            return

        h, w = image.shape[:2]

        window[
            rect.y:rect.y + h,
            rect.x:rect.x + w,
        ] = image
