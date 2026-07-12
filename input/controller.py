from input.board_mapper import BoardMapper


class Controller:

    def __init__(self, game_engine):

        self._game_engine = game_engine
        self._selected = None



    def click(self, x, y):

        position = BoardMapper.to_position(
            x,
            y
        )


        board = self._game_engine.get_board()


        if not board.is_inside(
            position[0],
            position[1]
        ):
            return



        if self._selected is None:

            piece = board.get(
                position[0],
                position[1]
            )


            if piece != ".":
                self._selected = position


            return



        self._game_engine.move_request(
            self._selected,
            position
        )


        self._selected = None