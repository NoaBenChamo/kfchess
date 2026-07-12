class GameState:

    def __init__(self, board):
        self._board = board
        self._selected = None
        self._game_over = False


    def get_board(self):
        return self._board


    def get_selected(self):
        return self._selected


    def set_selected(self, position):
        self._selected = position


    def is_game_over(self):
        return self._game_over


    def set_game_over(self):
        self._game_over = True