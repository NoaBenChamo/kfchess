from dataclasses import dataclass

from input.board_mapper import BoardMapper
from view.layout.game_layout import GameLayout
from view.layout.board_geometry import BoardGeometry
from view.assets.assets_manager import AssetsManager
from view.pieces.piece_animator import PieceAnimator
from view.pieces.piece_renderer import PieceRenderer
from view.board.board_renderer import BoardRenderer
from view.board.highlight_renderer import HighlightRenderer
from view.board.rest_overlay_renderer import RestOverlayRenderer
from view.hud.game_over_renderer import GameOverRenderer
from view.board.board_view import BoardView
from view.hud.header_view import HeaderView
from view.hud.footer_view import FooterView
from view.hud.player_view import PlayerView
from view.rendering.window_renderer import WindowRenderer


@dataclass(frozen=True)
class UiBundle:
    renderer: WindowRenderer
    board_mapper: BoardMapper


def create_ui(window_width, window_height) -> UiBundle:
    """
    Builds and wires all view-layer components.

    Returns:
        UiBundle with the window renderer and board mapper for input.
    """
    layout = GameLayout(window_width, window_height)
    board_rect = layout.board_rect

    assets_manager = AssetsManager(board_rect)
    board_geometry = BoardGeometry(board_rect)

    piece_animator = PieceAnimator(assets_manager)

    board_view = BoardView(
        board_renderer=BoardRenderer(board_rect, assets_manager),
        highlight_renderer=HighlightRenderer(board_geometry),
        piece_renderer=PieceRenderer(board_geometry, piece_animator),
        rest_overlay_renderer=RestOverlayRenderer(board_geometry),
        game_over_renderer=GameOverRenderer(),
    )

    renderer = WindowRenderer(
        layout=layout,
        header_view=HeaderView(),
        left_player_view=PlayerView("white"),
        board_view=board_view,
        right_player_view=PlayerView("black"),
        footer_view=FooterView(),
    )

    board_mapper = BoardMapper(board_rect)

    return UiBundle(
        renderer=renderer,
        board_mapper=board_mapper,
    )
