class PromotionRule:


    @staticmethod
    def should_promote(piece, position, board):

        if piece is None:
            return False


        if piece.type != "P":
            return False


        if piece.color == "W":
            return position.row == 0


        return position.row == len(board.get_rows()) - 1