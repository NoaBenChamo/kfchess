from rules.piece_rules.movement_rule import MovementRule


class PawnRule(MovementRule):

    def can_move(self, piece, source, target, board):

        direction = -1 if piece.color == "W" else 1

        row_change = target.row - source.row
        col_change = target.col - source.col


        return (
            row_change == direction
            and
            col_change == 0
        )