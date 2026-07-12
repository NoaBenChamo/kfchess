from realtime.clock import GameClock
from realtime.move import Move
from realtime.jump import Jump
from realtime.movement_validator import MovementValidator

from rules.capture_rule import CaptureRule
from rules.game_over_rule import GameOverRule
from rules.promotion_rule import PromotionRule

from config.constants import JUMP_DURATION


class RealTimeArbiter:

    def __init__(self, board):

        self._board = board
        self._clock = GameClock()

        self._active_moves = []
        self._active_jumps = []


    def add_move(self, move):

        self._active_moves.append(move)


    def wait(self, ms):

        self._clock.advance(ms)

        self.resolve_moves()


    def get_time(self):

        return self._clock.get_time()


    def is_moving(self, position):

        return MovementValidator.is_moving(
            self._active_moves,
            position
        )


    def resolve_moves(self):

        current_time = self._clock.get_time()

        finished = []


        for move in self._active_moves:

            if move.is_finished(current_time):

                self.finish_move(move)

                finished.append(move)


        for move in finished:

            self._active_moves.remove(move)



        finished_jumps = []

        for jump in self._active_jumps:

            if jump.is_finished(current_time):
                finished_jumps.append(jump)


        for jump in finished_jumps:
            self._active_jumps.remove(jump)



    def finish_move(self, move):

        jump = self.find_jump(
            move.target,
            move.piece
        )


        if jump:

            self._board.set(
                move.source[0],
                move.source[1],
                "."
            )


            self._board.set(
                jump.position[0],
                jump.position[1],
                jump.piece
            )


            self._active_jumps.remove(jump)

            return



        self._board.set(
            move.source[0],
            move.source[1],
            "."
        )


        target_piece = self._board.get(
            move.target[0],
            move.target[1]
        )


        if CaptureRule.can_capture(
            move.piece,
            target_piece
        ):

            self._board.set(
                move.target[0],
                move.target[1],
                move.piece
            )


            if PromotionRule.should_promote(
                move.piece,
                move.target,
                self._board
            ):

                self._board.set(
                    move.target[0],
                    move.target[1],
                    move.piece[0] + "Q"
                )


    def add_jump(self, jump):

        self._active_jumps.append(jump)


    def is_jumping(self, position):

        for jump in self._active_jumps:

            if jump.position == position:
                return True

        return False


    def find_jump(self, position, moving_piece):

        for jump in self._active_jumps:

            if (
                jump.position == position
                and
                jump.piece[0] != moving_piece[0]
            ):
                return jump


        return None