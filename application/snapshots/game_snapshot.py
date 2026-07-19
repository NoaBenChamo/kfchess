class GameSnapshot:

    def __init__(self, board_width, board_height, pieces, selected_cell, game_over,
                 white_moves=None, black_moves=None):
        self.board_width = board_width
        self.board_height = board_height
        self.pieces = pieces
        self.selected_cell = selected_cell
        self.game_over = game_over
        self.white_moves = white_moves or []
        self.black_moves = black_moves or []
