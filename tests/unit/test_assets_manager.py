import pytest

from model.piece_state import PieceState
from view.assets.assets_manager import AssetsManager
from view.layout.game_layout import GameLayout


def test_assets_manager_loads_board_and_idle_sprites():
    layout = GameLayout(1280, 900)
    assets = AssetsManager(layout.board_rect)

    board = assets.get_board()
    assert board is not None
    assert board.img is not None

    idle_frames = assets.get_piece_frames("wK", PieceState.IDLE)
    assert len(idle_frames) > 0
    assert idle_frames[0].img.shape[:2] == (
        layout.board_rect.cell_height,
        layout.board_rect.cell_width,
    )


def test_assets_manager_never_returns_empty_frames():
    layout = GameLayout(1280, 900)
    assets = AssetsManager(layout.board_rect)

    for state in PieceState:
        frames = assets.get_piece_frames("bQ", state)
        assert len(frames) > 0


def test_assets_manager_raises_when_board_image_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "view.assets.assets_manager.ASSETS_DIR",
        str(tmp_path),
    )

    layout = GameLayout(1280, 900)

    with pytest.raises(FileNotFoundError, match="Board image not found"):
        AssetsManager(layout.board_rect)
