import pytest

from model.board import Board
from model.piece import Piece
from model.position import Position

from rules.piece_rules.rook_rule import RookRule
from rules.piece_rules.bishop_rule import BishopRule
from rules.piece_rules.knight_rule import KnightRule
from rules.piece_rules.king_rule import KingRule
from rules.piece_rules.queen_rule import QueenRule
from rules.piece_rules.pawn_rule import PawnRule


def test_rook_horizontal_move():

    board = Board([
        [Piece("W", "R"), None, None]
    ])

    rule = RookRule()

    assert rule.can_move(
        Piece("W", "R"),
        Position(0, 0),
        Position(0, 2),
        board
    )


def test_rook_diagonal_move_is_illegal():

    board = Board([
        [Piece("W", "R"), None],
        [None, None]
    ])

    rule = RookRule()

    assert not rule.can_move(
        Piece("W", "R"),
        Position(0, 0),
        Position(1, 1),
        board
    )


def test_bishop_diagonal_move():

    board = Board([
        [Piece("W", "B"), None],
        [None, None]
    ])

    rule = BishopRule()

    assert rule.can_move(
        Piece("W", "B"),
        Position(0, 0),
        Position(1, 1),
        board
    )


def test_knight_l_move():

    board = Board([
        [Piece("W", "N"), None, None],
        [None, None, None],
        [None, None, None]
    ])

    rule = KnightRule()

    assert rule.can_move(
        Piece("W", "N"),
        Position(0, 0),
        Position(2, 1),
        board
    )


def test_king_single_step():

    board = Board([
        [Piece("W", "K"), None],
        [None, None]
    ])

    rule = KingRule()

    assert rule.can_move(
        Piece("W", "K"),
        Position(0, 0),
        Position(1, 1),
        board
    )


def test_queen_diagonal_move():

    board = Board([
        [Piece("W", "Q"), None],
        [None, None]
    ])

    rule = QueenRule()

    assert rule.can_move(
        Piece("W", "Q"),
        Position(0, 0),
        Position(1, 1),
        board
    )


def test_white_pawn_forward():

    board = Board([
        [None],
        [Piece("w", "P")]
    ])

    rule = PawnRule()

    assert rule.can_move(
        Piece("w", "P"),
        Position(1, 0),
        Position(0, 0),
        board
    )