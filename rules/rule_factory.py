from rules.piece_rules.king_rule import KingRule
from rules.piece_rules.queen_rule import QueenRule
from rules.piece_rules.rook_rule import RookRule
from rules.piece_rules.bishop_rule import BishopRule
from rules.piece_rules.knight_rule import KnightRule
from rules.piece_rules.pawn_rule import PawnRule


class RuleFactory:

    _rules = {
        "K": KingRule(),
        "Q": QueenRule(),
        "R": RookRule(),
        "B": BishopRule(),
        "N": KnightRule(),
        "P": PawnRule()
    }


    # מחזיר את אובייקט החוקים המתאים לכלי המבוקש
    @staticmethod
    def get(piece_type):
        return RuleFactory._rules[piece_type]