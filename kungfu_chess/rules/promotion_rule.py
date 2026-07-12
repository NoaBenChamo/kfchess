class PromotionRule:

    @staticmethod
    def should_promote(piece, target, board):
        last_row = 0 if piece[0] == "w" else len(board.get_rows()) - 1
        return piece[1] == "P" and target[0] == last_row
