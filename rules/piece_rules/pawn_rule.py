from rules.piece_rules.movement_rule import MovementRule


class PawnRule(MovementRule):

    def can_move(self, piece, source, target, board):

        direction = -1 if piece.color == "w" else 1

        row = target.row - source.row
        col = target.col - source.col


        # צעד רגיל
        if col == 0 and row == direction:

            return board.get(target) is None


        # שני צעדים מהתחלה
        if col == 0 and row == 2 * direction:

            middle = source.row + direction

            return (
                board.get(target) is None
                and
                board.get(
                    type(source)(
                        middle,
                        source.col
                    )
                ) is None
            )


        # אכילה באלכסון
        if abs(col) == 1 and row == direction:

            target_piece = board.get(target)

            return (
                target_piece is not None
                and
                target_piece.color != piece.color
            )


        return False