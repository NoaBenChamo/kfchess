from model.position import Position
from snapshots.piece_snapshot import PieceSnapshot


class Controller:
    """
    Translates user actions into PlaySession commands.

    Responsible for:
        - mapping screen coordinates to board positions
        - handling selection flow
        - forwarding move and jump requests to the session

  Selection behavior:
        - First click selects a piece (session decides whether selection is valid).
        - Second click on another friendly piece swaps selection.
        - Second click elsewhere requests a move to that square.
        - Move requests are forwarded without assuming synchronous success.
    """

    def __init__(self, session, board_mapper):
        self._session = session
        self._board_mapper = board_mapper

    def click(self, x, y):
        """
        Handles a left-click in full-window pixel coordinates.
        """
        position = self._board_mapper.to_position(x, y)

        if position is None:
            return

        selected = self._session.get_selected()

        if selected is None:
            self._session.select(position)
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

        self._session.request_jump_to(position)

    def wait(self, ms):
        """
        Advances session time by the given number of milliseconds.
        """
        self._session.pump(ms)

    def tick(self, ms):
        """
        Backward-compatible alias for wait().
        """
        self.wait(ms)

    def get_board(self):
        """
        Returns the local board model when the session supports it.
        """
        getter = getattr(self._session, "get_board", None)
        if getter is None:
            raise RuntimeError("get_board is only available in local mode")
        return getter()

    def _handle_selected_click(
        self,
        selected_position,
        clicked_position,
    ):
        snapshot = self._session.create_snapshot()
        selected_piece = self._piece_at(snapshot, selected_position)
        clicked_piece = self._piece_at(snapshot, clicked_position)

        if selected_piece is None:
            self._session.clear_selection()
            return

        if self._is_other_friendly_piece(
            selected_piece=selected_piece,
            clicked_piece=clicked_piece,
            selected_position=selected_position,
            clicked_position=clicked_position,
        ):
            self._session.clear_selection()
            self._session.select(clicked_position)
            return

        self._session.request_move_to(clicked_position)

    @staticmethod
    def _piece_at(snapshot, position):
        for piece in snapshot.pieces:
            if piece.position.row == position.row and piece.position.col == position.col:
                return piece
        return None

    @staticmethod
    def _is_other_friendly_piece(
        selected_piece,
        clicked_piece,
        selected_position,
        clicked_position,
    ):
        return (
            isinstance(selected_piece, PieceSnapshot)
            and clicked_piece is not None
            and selected_piece.color == clicked_piece.color
            and selected_position != clicked_position
        )
