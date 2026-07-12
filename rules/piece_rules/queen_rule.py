from rules.piece_rules.movement_rule import MovementRule
from rules.piece_rules.rook_rule import RookRule
from rules.piece_rules.bishop_rule import BishopRule


class QueenRule(MovementRule):

    def can_move(self, piece, source, target, board):

        return (
            RookRule().can_move(
                piece,
                source,
                target,
                board
            )
            or
            BishopRule().can_move(
                piece,
                source,
                target,
                board
            )
        )