from rules.piece_rules.movement_rule import MovementRule
from rules.path_checker import PathChecker

#חוקיות ההזזה של הרץ
class BishopRule(MovementRule):

    # בודק אם הרץ יכול לזוז באלכסון והנתיב פנוי
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

        diagonal = (
            abs(target.row - source.row)
            ==
            abs(target.col - source.col)
        )

        return (
            diagonal
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
