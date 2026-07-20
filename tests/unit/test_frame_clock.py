from config.constants import FRAME_DURATION_MS
from view.frame_clock import FrameClock
from view.pieces.piece_animator import PieceAnimator


def test_frame_clock_starts_at_zero():
    clock = FrameClock()

    assert clock.now_ms() == 0


def test_frame_clock_accumulates_ticks():
    clock = FrameClock()

    clock.tick(16)
    clock.tick(16)

    assert clock.now_ms() == 32


def test_frame_clock_reset():
    clock = FrameClock()
    clock.tick(100)

    clock.reset()

    assert clock.now_ms() == 0


def test_piece_animator_frame_index_is_deterministic():
    assert PieceAnimator.frame_index(0) == 0
    assert PieceAnimator.frame_index(FRAME_DURATION_MS - 1) == 0
    assert PieceAnimator.frame_index(FRAME_DURATION_MS) == 1


def test_piece_animator_returns_same_frame_for_same_time():
    class FakeAssetsManager:
        def get_piece_frames(self, piece_key, state):
            return ["a", "b", "c"]

    class FakePiece:
        color = "w"
        piece_type = "K"
        state = "idle"

    animator = PieceAnimator(FakeAssetsManager())
    piece = FakePiece()

    first = animator.current_frame(piece, 300)
    second = animator.current_frame(piece, 300)

    assert first == second
    assert first == "c"
