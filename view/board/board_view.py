class BoardView:
    """
    Coordinates the rendering of the board.

    Rendering order:
        1. Static board
        2. Selected-cell highlight
        3. Chess pieces
        4. Rest/cooldown overlays
        5. Game over overlay
    """

    def __init__(
        self,
        board_rect,
        canvas_width,
        canvas_height,
        board_renderer,
        highlight_renderer,
        piece_renderer,
        rest_overlay_renderer,
        game_over_renderer,
    ):
        self._board_rect = board_rect
        self._canvas_width = canvas_width
        self._canvas_height = canvas_height

        self._board_renderer = board_renderer
        self._highlight_renderer = highlight_renderer
        self._piece_renderer = piece_renderer
        self._rest_overlay_renderer = rest_overlay_renderer
        self._game_over_renderer = game_over_renderer

        self._canvas = None

    def render(self, snapshot):
        """
        Renders one complete board frame.
        """
        self._canvas = self._board_renderer.create_canvas(
            canvas_width=self._canvas_width,
            canvas_height=self._canvas_height,
        )

        self._highlight_renderer.render(
            canvas=self._canvas,
            selected_cell=snapshot.selected_cell,
        )

        self._piece_renderer.render(
            canvas=self._canvas,
            pieces=snapshot.pieces,
        )

        self._rest_overlay_renderer.render(
            canvas=self._canvas,
            pieces=snapshot.pieces,
        )

        if snapshot.game_over:
            self._game_over_renderer.render(
                self._canvas
            )

    def get_canvas(self):
        """
        Returns the rendered board canvas.
        """
        return self._canvas

    @property
    def board_rect(self):
        return self._board_rect

    @property
    def canvas_width(self):
        return self._canvas_width

    @property
    def canvas_height(self):
        return self._canvas_height