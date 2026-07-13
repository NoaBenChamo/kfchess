from rules.piece_rules.movement_rule import MovementRule

#חוקיות ההזזה של הסוס
class KnightRule(MovementRule):

    # בודק אם הפרש יכול לזוז בצורת L ולקפוץ מעל כלים
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

        return (
            (row == 2 and col == 1)
            or
            (row == 1 and col == 2)
        )
