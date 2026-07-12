class GameState:

    def __init__(self, board):

        self.board = board
        self.selected = None
        self.game_over = False


    def select(self, position):

        self.selected = position


    def clear_selection(self):

        self.selected = None


    def set_game_over(self):

        self.game_over = True