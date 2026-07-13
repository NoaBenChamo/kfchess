from rules.piece_rules.movement_rule import MovementRule

#חוקיות ההזזה של המלך
class KingRule(MovementRule):

    # בודק אם המלך יכול לזוז צעד אחד בכל כיוון
    def can_move(
        self,
        piece,
        source,
        target,
        board,
        active_moves=None,
        move_start_time=None,
        move_duration=None
    ):

        row = abs(target.row - source.row)
        col = abs(target.col - source.col)

        return max(row, col) == 1
