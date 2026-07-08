class PawnRule:


    def can_move(self, piece, source, target, board):

        direction = -1 if piece[0] == "w" else 1

        row_diff = target[0] - source[0]
        col_diff = abs(target[1] - source[1])

        target_piece = board.get(
            target[0],
            target[1]
        )


        # תנועה רגילה קדימה
        if col_diff == 0:

            return (
                row_diff == direction
                and
                target_piece == "."
            )


        # אכילה באלכסון
        if col_diff == 1:

            return (
                row_diff == direction
                and
                target_piece != "."
                and
                target_piece[0] != piece[0]
            )


        return False