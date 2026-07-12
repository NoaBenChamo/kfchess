from rules.king_rule import KingRule
from rules.queen_rule import QueenRule
from rules.rook_rule import RookRule
from rules.bishop_rule import BishopRule
from rules.knight_rule import KnightRule
from rules.pawn_rule import PawnRule


class RuleFactory:

    rules = {
        "K": KingRule(),
        "Q": QueenRule(),
        "R": RookRule(),
        "B": BishopRule(),
        "N": KnightRule(),
        "P": PawnRule()
    }

    @staticmethod
    def get(piece_type):
        return RuleFactory.rules[piece_type]
