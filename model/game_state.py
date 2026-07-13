#מייצג את מצב המשחק הנוכחי, כולל הלוח, המיקום הנבחר והאם המשחק הסתיים
class GameState:

    def __init__(self, board):

        self.board = board
        self.selected = None
        self.game_over = False


    # קובע את המיקום הנבחר כרגע
    def select(self, position):
        self.selected = position


    # מנקה את הבחירה הנוכחית
    def clear_selection(self):
        self.selected = None


    # מסמן את המשחק כהסתיים
    def set_game_over(self):
        self.game_over = True