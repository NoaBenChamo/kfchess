from rules.piece_rules.movement_rule import MovementRule
from rules.path_checker import PathChecker


class BishopRule(MovementRule):

    def can_move(self, piece, source, target, board):

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
                target
            )
        )