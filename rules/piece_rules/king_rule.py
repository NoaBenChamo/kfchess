from rules.piece_rules.movement_rule import MovementRule

class KingRule(MovementRule):

    def can_move(self, piece, source, target, board):

        row = abs(target.row - source.row)
        col = abs(target.col - source.col)

        return max(row, col) == 1