class GameSnapshot:

    def __init__(self, board_width, board_height, pieces, selected_cell, game_over):
        self.board_width = board_width
        self.board_height = board_height
        self.pieces = pieces
        self.selected_cell = selected_cell
        self.game_over = game_over
