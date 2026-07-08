from movement.piece_rules.king_rule import KingRule
from movement.piece_rules.queen_rule import QueenRule
from movement.piece_rules.rook_rule import RookRule
from movement.piece_rules.bishop_rule import BishopRule
from movement.piece_rules.knight_rule import KnightRule
from movement.piece_rules.pawn_rule import PawnRule


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