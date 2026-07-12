from rules.rule_factory import RuleFactory


class RuleEngine:


    def is_valid_move(self, piece, source, target, board):

        if piece is None:
            return False


        rule = RuleFactory.get(
            piece.type
        )


        return rule.can_move(
            piece,
            source,
            target,
            board
        )