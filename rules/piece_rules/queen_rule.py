from rules.piece_rules.movement_rule import MovementRule
from rules.piece_rules.rook_rule import RookRule
from rules.piece_rules.bishop_rule import BishopRule

#חוקיות ההזזה של המלכה
class QueenRule(MovementRule):

    # בודק אם המלכה יכולה לזוז בקו ישר או אלכסוני
    def can_move(
        self,
        piece,
        source,
        target,
        board,
        active_moves=None,
        move_start_time=None,
        move_duration=None
    ):

        return (
            RookRule().can_move(
                piece,
                source,
                target,
                board,
                active_moves,
                move_start_time,
                move_duration
            )
            or
            BishopRule().can_move(
                piece,
                source,
                target,
                board,
                active_moves,
                move_start_time,
                move_duration
            )
        )
