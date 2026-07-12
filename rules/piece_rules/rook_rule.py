from rules.piece_rules.movement_rule import MovementRule
from rules.path_checker import PathChecker


class RookRule(MovementRule):

    def can_move(self, piece, source, target, board):

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
                target
            )
        )