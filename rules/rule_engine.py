
from rules.rule_factory import RuleFactory


class RuleEngine:

    @staticmethod
    def validate_move(piece, source, target, board):

        rule = RuleFactory.get(piece[1])

        return rule.can_move(
            piece,
            source,
            target,
            board
        )