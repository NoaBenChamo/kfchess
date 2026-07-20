from model.piece_state import PieceState
from model.position import Position
from input.board_rect import BoardRect
from view.layout.board_geometry import BoardGeometry
from view.pieces.piece_renderer import PieceRenderer


class FakeAnimator:
    def current_frame(self, piece, animation_time_ms):
        return None


def _renderer():
    board_rect = BoardRect(0, 0, 800, 800, 8, 8)
    geometry = BoardGeometry(board_rect)
    return PieceRenderer(geometry, FakeAnimator())


class FakePiece:
    def __init__(
        self,
        position,
        state=PieceState.IDLE,
        target=None,
        progress=None,
    ):
        self.position = position
        self.state = state
        self.target = target
        self.progress = progress


def test_idle_piece_stays_on_cell_origin():
    renderer = _renderer()
    piece = FakePiece(Position(2, 3))

    x, y = renderer._piece_position(piece)

    assert x == renderer._geometry.position_to_local(piece.position)[0]
    assert y == renderer._geometry.position_to_local(piece.position)[1]


def test_move_piece_is_halfway_between_source_and_target():
    renderer = _renderer()
    piece = FakePiece(
        Position(0, 0),
        state=PieceState.MOVE,
        target=Position(0, 4),
        progress=0.5,
    )

    x, y = renderer._piece_position(piece)
    start_x, start_y = renderer._geometry.position_to_local(piece.position)
    target_x, target_y = renderer._geometry.position_to_local(piece.target)

    assert x == start_x + (target_x - start_x) // 2
    assert y == start_y


def test_jump_piece_rises_and_returns_to_same_x():
    renderer = _renderer()
    at_start = FakePiece(
        Position(1, 1),
        state=PieceState.JUMP,
        progress=0.0,
    )
    at_peak = FakePiece(
        Position(1, 1),
        state=PieceState.JUMP,
        progress=0.5,
    )
    at_end = FakePiece(
        Position(1, 1),
        state=PieceState.JUMP,
        progress=1.0,
    )

    start_x, start_y = renderer._piece_position(at_start)
    peak_x, peak_y = renderer._piece_position(at_peak)
    end_x, end_y = renderer._piece_position(at_end)

    assert start_x == peak_x == end_x
    assert peak_y < start_y
    assert end_y == start_y
