from kungfu_chess.rules.king_rule import KingRule
from kungfu_chess.rules.queen_rule import QueenRule
from kungfu_chess.rules.rook_rule import RookRule
from kungfu_chess.rules.bishop_rule import BishopRule
from kungfu_chess.rules.knight_rule import KnightRule
from kungfu_chess.rules.pawn_rule import PawnRule


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
