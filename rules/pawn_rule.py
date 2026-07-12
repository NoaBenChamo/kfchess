from config.constants import PAWN_START_ROW

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
            if row_diff == direction and target_piece == ".":
                return True

            board_rows = len(board.get_rows())
            start_row = board_rows - 1 if piece[0] == "w" else 0

            middle = board.get(source[0] + direction, source[1])

            return (
                row_diff == 2 * direction
                and source[0] == start_row
                and target_piece == "."
                and middle == "."
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