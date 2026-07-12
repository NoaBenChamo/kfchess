from realtime.clock import GameClock
from realtime.movement_validator import MovementValidator
from rules.capture_rule import CaptureRule
from rules.game_over_rule import GameOverRule
from rules.promotion_rule import PromotionRule


class RealTimeArbiter:

    def __init__(self, board):
        self._board = board
        self._clock = GameClock()
        self._active_moves = []
        self._active_jumps = []
        self._game_events = []

    def add_move(self, move):
        self._active_moves.append(move)

    def wait(self, ms):
        self._clock.advance(ms)
        self.resolve_finished_moves()
        self.resolve_finished_jumps()

    def get_time(self):
        return self._clock.get_time()

    def is_moving(self, position):
        return MovementValidator.is_moving(
            self._active_moves,
            position
        )

    def resolve_finished_moves(self):

        current_time = self._clock.get_time()
        finished = []

        for move in self._active_moves:

            if move.is_finished(current_time):
                self.finish_move(move)
                finished.append(move)

        for move in finished:
            self._active_moves.remove(move)

    def finish_move(self, move):

        target_piece = self._board.get(move.target)

        if target_piece is not None:

            if not CaptureRule.can_capture(
                move.piece,
                target_piece
            ):
                return

        self._board.set(
            move.source,
            None
        )

        self._board.set(
            move.target,
            move.piece
        )

        if PromotionRule.should_promote(
            move.piece,
            move.target,
            self._board
        ):
            move.piece.type = "Q"

        if (
            target_piece is not None
            and
            GameOverRule.is_king_captured(target_piece)
        ):
            self._game_events.append(
                "GAME_OVER"
            )

    def resolve_finished_jumps(self):

        current_time = self._clock.get_time()
        finished = []

        for jump in self._active_jumps:

            if jump.is_finished(current_time):
                finished.append(jump)

        for jump in finished:
            self._active_jumps.remove(jump)

    def get_events(self):

        events = self._game_events[:]
        self._game_events.clear()
        return events