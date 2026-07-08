from movement.rook_rule import RookRule
from movement.bishop_rule import BishopRule


class QueenRule:

    def can_move(self, source, target):

        return (
            RookRule().can_move(source, target)
            or
            BishopRule().can_move(source, target)
        )