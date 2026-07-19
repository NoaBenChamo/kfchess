class Controller:
    """
    Translates user actions into GameEngine commands.

    Responsible for:
        - mapping screen coordinates to board positions
        - handling selection flow
        - forwarding move, jump and time commands to the engine
    """

    def __init__(self, game_engine, board_mapper):
        self._game_engine = game_engine
        self._board_mapper = board_mapper

    def click(self, x, y):
        """
        Handles a left-click in full-window pixel coordinates.
        """
        position = self._board_mapper.to_position(x, y)

        if position is None:
            return

        selected = self._game_engine.get_selected()

        if selected is None:
            self._game_engine.select(position)
            return

        self._handle_selected_click(
            selected_position=selected,
            clicked_position=position,
        )

    def jump(self, x, y):
        """
        Handles a right-click jump request.
        """
        position = self._board_mapper.to_position(x, y)

        if position is None:
            return

        self._game_engine.jump(position)

    def tick(self, ms):
        """
        Advances game time by the given number of milliseconds.
        """
        self._game_engine.tick(ms)

    def wait(self, ms):
        """
        Backward-compatible alias for tick().
        """
        self.tick(ms)

    def get_board(self):
        """
        Returns the current board model.
        """
        return self._game_engine.get_board()

    def _handle_selected_click(
        self,
        selected_position,
        clicked_position,
    ):
        board = self._game_engine.get_board()

        selected_piece = board.get(selected_position)
        clicked_piece = board.get(clicked_position)

        if self._is_other_friendly_piece(
            selected_piece=selected_piece,
            clicked_piece=clicked_piece,
            selected_position=selected_position,
            clicked_position=clicked_position,
        ):
            self._replace_selection(clicked_position)
            return

        self._game_engine.move_request(clicked_position)

    def _replace_selection(self, position):
        self._game_engine.clear_selection()
        self._game_engine.select(position)

    @staticmethod
    def _is_other_friendly_piece(
        selected_piece,
        clicked_piece,
        selected_position,
        clicked_position,
    ):
        return (
            selected_piece is not None
            and clicked_piece is not None
            and selected_piece.color == clicked_piece.color
            and selected_position != clicked_position
        )