from movement.piece_rules.rook_rule import RookRule
from movement.piece_rules.bishop_rule import BishopRule


class QueenRule:

    def can_move(self, piece, source, target, board):

        return (
            RookRule().can_move(source, target)
            or
            BishopRule().can_move(source, target)
        )