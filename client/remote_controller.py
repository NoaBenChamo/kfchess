from client.snapshot_codec import piece_at
from shared.squares import position_to_square


class RemoteController:
    """
    Local UI selection + network move requests. No GameEngine.
    """

    def __init__(self, session, board_mapper):
        self._session = session
        self._board_mapper = board_mapper

    def click(self, x, y):
        position = self._board_mapper.to_position(x, y)
        if position is None:
            return

        state = self._session.state
        selected = state.selected

        if selected is None:
            if piece_at(state.snapshot_dict, position) is None:
                return
            state.select(position)
            return

        piece = piece_at(state.snapshot_dict, selected)
        if piece is None:
            state.clear_selection()
            return

        clicked = piece_at(state.snapshot_dict, position)
        if (
            clicked is not None
            and clicked[0] == piece[0]
            and selected != position
        ):
            state.clear_selection()
            state.select(position)
            return

        color, piece_type = piece
        command = (
            f"{color.upper()}{piece_type}"
            f"{position_to_square(selected)}"
            f"{position_to_square(position)}"
        )
        self._session.send_move(command)
        state.clear_selection()

    def jump(self, x, y):
        # Jump over the network is not wired in B.5 yet.
        return
