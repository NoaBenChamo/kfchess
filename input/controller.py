from model.position import Position



class Controller:


    def __init__(self, game_engine):

        self._game_engine = game_engine

        self._selected = None



    def click(self, x, y):

        position = Position(
            y // 100,
            x // 100
        )


        if self._selected is None:

            self._game_engine.select(
                position
            )

            self._selected = position

        else:

            self._game_engine.move_request(
                position
            )

            self._selected = None



    def wait(self, ms):

        self._game_engine.wait(ms)



    def get_board(self):

        return self._game_engine.get_board()
    
    def jump(self, x, y):

        self._game_engine.jump(
            x,
            y
        )