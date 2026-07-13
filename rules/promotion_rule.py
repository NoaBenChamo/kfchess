#בדיקה האם חייל צריך לקבל הכתרה למלכה
class PromotionRule:


    # T/F בודק האם החייל הגיע לשורה האחרונה של היריב ומחזיר 
    @staticmethod
    def should_promote(piece, position, board):

        if piece is None:
            return False

        # רק רגלים מתקדמים
        if piece.type != "P":
            return False

        num_rows = len(board.get_rows())

        # לבן מתקדם בשורה 0, שחור בשורה האחרונה
        if piece.color == "w":
            return position.row == 0

        if piece.color == "b":
            return position.row == num_rows - 1

        return False
