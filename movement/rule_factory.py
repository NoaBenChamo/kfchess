from movement.king_rule import KingRule
from movement.queen_rule import QueenRule
from movement.rook_rule import RookRule
from movement.bishop_rule import BishopRule
from movement.knight_rule import KnightRule


class RuleFactory:

    rules = {
        "K": KingRule(),
        "Q": QueenRule(),
        "R": RookRule(),
        "B": BishopRule(),
        "N": KnightRule()
    }


    @staticmethod
    def get(piece_type):

        return RuleFactory.rules[piece_type]