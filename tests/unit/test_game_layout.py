from config.constants import FOOTER_HEIGHT, HEADER_HEIGHT, PLAYER_WIDTH
from input.screen_rect import ScreenRect
from view.game_view.game_layout import GameLayout


def test_screen_rect_exposes_its_geometry():
    rect = ScreenRect(10, 20, 300, 400)

    assert rect.x == 10
    assert rect.y == 20
    assert rect.width == 300
    assert rect.height == 400


def test_game_layout_uses_screen_rects_for_screen_regions():
    layout = GameLayout(1280, 900)

    assert isinstance(layout.board_canvas_rect, ScreenRect)
    assert isinstance(layout.header_rect, ScreenRect)
    assert isinstance(layout.footer_rect, ScreenRect)
    assert isinstance(layout.left_player_rect, ScreenRect)
    assert isinstance(layout.right_player_rect, ScreenRect)

    assert layout.header_rect.x == 0
    assert layout.header_rect.y == 0
    assert layout.header_rect.width == 1280
    assert layout.header_rect.height == HEADER_HEIGHT

    assert layout.footer_rect.y == 900 - FOOTER_HEIGHT
    assert layout.left_player_rect.width == PLAYER_WIDTH
    assert layout.right_player_rect.width == PLAYER_WIDTH
    assert layout.board_canvas_rect.x == PLAYER_WIDTH
    assert layout.board_canvas_rect.y == HEADER_HEIGHT
