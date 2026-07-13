from rules.rule_factory import RuleFactory

#מנהל את בידיקת חוקיות ההזזה לפי הכללים של הכלי המבוקש
class RuleEngine:

    # בודק אם ההזזה חוקית לפי הכללים של הכלי
    def is_valid_move(
        self,
        piece,
        source,
        target,
        board,
        active_moves=None,
        move_start_time=None,
        move_duration=None
    ):

        if piece is None:
            return False

        rule = RuleFactory.get(piece.type)

        return rule.can_move(
            piece,
            source,
            target,
            board,
            active_moves,
            move_start_time,
            move_duration
        )
