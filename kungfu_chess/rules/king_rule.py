from kungfu_chess.rules.movement_rule import MovementRule


class KingRule(MovementRule):

    def can_move(self, piece, source, target, board):

        row_diff = abs(target[0] - source[0])
        col_diff = abs(target[1] - source[1])

        return (
            row_diff <= 1
            and
            col_diff <= 1
            and
            (row_diff != 0 or col_diff != 0)
        )
