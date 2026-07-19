from model.board import Board
from model.piece import Piece
from model.position import Position

from input.board_rect import BoardRect
from input.board_mapper import BoardMapper
from input.controller import Controller
from engine.game_engine import GameEngine


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _init_mapper(x=0, y=0, board_w=800, board_h=800, cols=8, rows=8):
    BoardMapper.init(BoardRect(x, y, board_w, board_h, cols, rows))


# ------------------------------------------------------------------ #
# BoardRect                                                            #
# ------------------------------------------------------------------ #

def test_board_rect_contains_inside():
    rect = BoardRect(100, 50, 800, 800, 8, 8)
    assert rect.contains(100, 50)
    assert rect.contains(500, 400)
    assert rect.contains(899, 849)


def test_board_rect_contains_outside():
    rect = BoardRect(100, 50, 800, 800, 8, 8)
    assert not rect.contains(99, 50)
    assert not rect.contains(100, 49)
    assert not rect.contains(900, 400)
    assert not rect.contains(400, 850)


def test_board_rect_cell_size():
    rect = BoardRect(0, 0, 800, 800, 8, 8)
    assert rect.cell_w == 100
    assert rect.cell_h == 100


# ------------------------------------------------------------------ #
# BoardMapper — zero offset (default)                                  #
# ------------------------------------------------------------------ #

def test_to_position_top_left_cell():
    _init_mapper()
    assert BoardMapper.to_position(0, 0) == Position(0, 0)


def test_to_position_bottom_right_cell():
    _init_mapper()
    assert BoardMapper.to_position(799, 799) == Position(7, 7)


def test_to_position_outside_board_returns_none():
    _init_mapper()
    assert BoardMapper.to_position(800, 0)  is None
    assert BoardMapper.to_position(0, 800)  is None
    assert BoardMapper.to_position(-1, 0)   is None
    assert BoardMapper.to_position(0, -1)   is None


# ------------------------------------------------------------------ #
# BoardMapper — non-zero X offset                                      #
# ------------------------------------------------------------------ #

def test_to_position_with_x_offset_top_left():
    _init_mapper(x=160, y=0)
    # canvas pixel (160, 0) → board local (0, 0) → Position(0, 0)
    assert BoardMapper.to_position(160, 0) == Position(0, 0)


def test_to_position_with_x_offset_second_column():
    _init_mapper(x=160, y=0)
    # canvas pixel (260, 0) → board local (100, 0) → col 1
    assert BoardMapper.to_position(260, 0) == Position(0, 1)


def test_to_position_with_x_offset_outside_left():
    _init_mapper(x=160, y=0)
    assert BoardMapper.to_position(159, 0) is None


def test_to_position_with_x_offset_outside_right():
    _init_mapper(x=160, y=0)
    assert BoardMapper.to_position(160 + 800, 0) is None


# ------------------------------------------------------------------ #
# BoardMapper — non-zero Y offset                                      #
# ------------------------------------------------------------------ #

def test_to_position_with_y_offset_top_left():
    _init_mapper(x=0, y=40)
    assert BoardMapper.to_position(0, 40) == Position(0, 0)


def test_to_position_with_y_offset_second_row():
    _init_mapper(x=0, y=40)
    assert BoardMapper.to_position(0, 140) == Position(1, 0)


def test_to_position_with_y_offset_outside_above():
    _init_mapper(x=0, y=40)
    assert BoardMapper.to_position(0, 39) is None


def test_to_position_with_y_offset_outside_below():
    _init_mapper(x=0, y=40)
    assert BoardMapper.to_position(0, 40 + 800) is None


# ------------------------------------------------------------------ #
# BoardMapper — combined X+Y offset (realistic GameLayout values)      #
# ------------------------------------------------------------------ #

def test_to_position_combined_offset_top_left():
    _init_mapper(x=160, y=40)
    assert BoardMapper.to_position(160, 40) == Position(0, 0)


def test_to_position_combined_offset_bottom_right():
    _init_mapper(x=160, y=40)
    assert BoardMapper.to_position(959, 839) == Position(7, 7)


def test_to_position_combined_offset_outside():
    _init_mapper(x=160, y=40)
    assert BoardMapper.to_position(0, 0)    is None   # header+player area
    assert BoardMapper.to_position(159, 40) is None   # left player panel
    assert BoardMapper.to_position(160, 39) is None   # header


# ------------------------------------------------------------------ #
# BoardMapper — to_pixels round-trip                                   #
# ------------------------------------------------------------------ #

def test_to_pixels_top_left():
    _init_mapper(x=160, y=40)
    assert BoardMapper.to_pixels(Position(0, 0)) == (160, 40)


def test_to_pixels_bottom_right():
    _init_mapper(x=160, y=40)
    assert BoardMapper.to_pixels(Position(7, 7)) == (160 + 700, 40 + 700)


def test_round_trip_position_to_pixels_to_position():
    _init_mapper(x=160, y=40)
    for row in range(8):
        for col in range(8):
            pos = Position(row, col)
            px, py = BoardMapper.to_pixels(pos)
            assert BoardMapper.to_position(px, py) == pos


# ------------------------------------------------------------------ #
# Controller — clicks outside board are ignored                        #
# ------------------------------------------------------------------ #

def test_controller_click_outside_board_ignored():
    _init_mapper(x=160, y=40)
    board = Board([[Piece("w", "R"), None]])
    engine = GameEngine(board)
    controller = Controller(engine)

    # click in the left player panel (x < 160)
    controller.click(50, 50)
    assert engine.get_selected() is None


def test_controller_click_inside_board_selects():
    _init_mapper(x=160, y=40)
    board = Board([[Piece("w", "R"), None]])
    engine = GameEngine(board)
    controller = Controller(engine)

    # click at canvas (160, 40) → board Position(0, 0)
    controller.click(160, 40)
    assert engine.get_selected() == Position(0, 0)


# ------------------------------------------------------------------ #
# Geometry consistency: same BoardRect used for rendering and input    #
# ------------------------------------------------------------------ #

def test_board_mapper_rect_matches_after_init():
    rect = BoardRect(160, 40, 800, 800, 8, 8)
    BoardMapper.init(rect)
    assert BoardMapper.get_rect() is rect


def test_to_pixels_and_to_position_use_same_rect():
    """
    A pixel produced by to_pixels must map back to the same Position
    regardless of board offset.
    """
    for ox, oy in [(0, 0), (160, 40), (200, 100)]:
        _init_mapper(x=ox, y=oy)
        pos = Position(3, 5)
        px, py = BoardMapper.to_pixels(pos)
        assert BoardMapper.to_position(px, py) == pos
