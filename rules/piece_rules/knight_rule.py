from rules.piece_rules.movement_rule import MovementRule


class KnightRule(MovementRule):

    def can_move(self, piece, source, target, board):

        row = abs(target.row - source.row)
        col = abs(target.col - source.col)

        return (
            (row == 2 and col == 1)
            or
            (row == 1 and col == 2)
        )