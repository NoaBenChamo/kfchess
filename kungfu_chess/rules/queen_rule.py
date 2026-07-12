from kungfu_chess.rules.rook_rule import RookRule
from kungfu_chess.rules.bishop_rule import BishopRule


class QueenRule:

    def can_move(self, piece, source, target, board):
        return (
            RookRule().can_move(piece, source, target, board)
            or
            BishopRule().can_move(piece, source, target, board)
        )
