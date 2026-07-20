from input.board_rect import BoardRect
from model.position import Position
from view.layout.board_geometry import BoardGeometry
from config.constants import LABEL_MARGIN


def _geometry():
    board_rect = BoardRect(
        x=100,
        y=60,
        width=640,
        height=640,
        cols=8,
        rows=8,
    )
    return BoardGeometry(board_rect)


def test_position_zero_maps_to_top_left_cell():
    geometry = _geometry()

    x, y = geometry.position_to_local(Position(0, 0))

    assert x == LABEL_MARGIN
    assert y == 0


def test_cell_center_is_inside_cell():
    geometry = _geometry()
    cell_w = geometry.cell_width
    cell_h = geometry.cell_height

    cx, cy = geometry.cell_center_to_local(Position(3, 4))

    x, y = geometry.position_to_local(Position(3, 4))

    assert x <= cx < x + cell_w
    assert y <= cy < y + cell_h


def test_local_coordinates_increase_with_row_and_col():
    geometry = _geometry()

    x0, y0 = geometry.cell_to_local(0, 0)
    x1, y1 = geometry.cell_to_local(0, 1)
    x2, y2 = geometry.cell_to_local(1, 0)

    assert x1 == x0 + geometry.cell_width
    assert y2 == y0 + geometry.cell_height
