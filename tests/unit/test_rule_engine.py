import pytest

from rules.rule_factory import RuleFactory
from rules.piece_rules.king_rule import KingRule
from rules.piece_rules.queen_rule import QueenRule
from rules.piece_rules.rook_rule import RookRule
from rules.piece_rules.bishop_rule import BishopRule
from rules.piece_rules.knight_rule import KnightRule
from rules.piece_rules.pawn_rule import PawnRule


def test_get_king_rule():

    rule = RuleFactory.get("K")

    assert isinstance(rule, KingRule)


def test_get_queen_rule():

    rule = RuleFactory.get("Q")

    assert isinstance(rule, QueenRule)


def test_get_rook_rule():

    rule = RuleFactory.get("R")

    assert isinstance(rule, RookRule)


def test_get_bishop_rule():

    rule = RuleFactory.get("B")

    assert isinstance(rule, BishopRule)


def test_get_knight_rule():

    rule = RuleFactory.get("N")

    assert isinstance(rule, KnightRule)


def test_get_pawn_rule():

    rule = RuleFactory.get("P")

    assert isinstance(rule, PawnRule)


def test_same_instance_returned():

    rule1 = RuleFactory.get("R")
    rule2 = RuleFactory.get("R")

    assert rule1 is rule2


def test_unknown_piece_raises_key_error():

    with pytest.raises(KeyError):
        RuleFactory.get("X")