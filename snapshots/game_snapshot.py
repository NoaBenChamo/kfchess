class GameSnapshot:

    def __init__(
        self,
        board_width,
        board_height,
        pieces,
        selected_cell,
        game_over,
        white_moves=None,
        black_moves=None,
        white_score=0,
        black_score=0,
        white_username=None,
        black_username=None,
        white_rating=None,
        black_rating=None,
        hud_line=None,
    ):
        self.board_width = board_width
        self.board_height = board_height
        self.pieces = pieces
        self.selected_cell = selected_cell
        self.game_over = game_over
        self.white_moves = white_moves or []
        self.black_moves = black_moves or []
        self.white_score = white_score
        self.black_score = black_score
        self.white_username = white_username
        self.black_username = black_username
        self.white_rating = white_rating
        self.black_rating = black_rating
        self.hud_line = hud_line
