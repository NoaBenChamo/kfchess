from rules.piece_rules.movement_rule import MovementRule
from rules.path_checker import PathChecker

#חוקיות ההזזה של הצריח
class RookRule(MovementRule):

    # בודק אם הצריח יכול לזוז בקו ישר והנתיב פנוי
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

        straight = (
            source.row == target.row
            or
            source.col == target.col
        )

        return (
            straight
            and
            PathChecker.clear(
                board,
                source,
                target,
                active_moves,
                move_start_time,
                move_duration
            )
        )
