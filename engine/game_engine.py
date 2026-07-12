from rules.rule_engine import RuleEngine
from rules.capture_rule import CaptureRule
from rules.game_over_rule import GameOverRule
from rules.promotion_rule import PromotionRule

from realtime.move import Move
from realtime.real_time_arbiter import RealTimeArbiter
from realtime.movement_time import MovementTime

from model.game_state import GameState


class Game:

    def __init__(self, board):

        self._state = GameState(board)

        self._rule_engine = RuleEngine()

        self._arbiter = RealTimeArbiter(board)


    def move_request(self, source, target):

        board = self._state.get_board()


        piece = board.get(
            source[0],
            source[1]
        )


        if piece == ".":
            return


        if not self._rule_engine.validate_move(
            piece,
            source,
            target,
            board
        ):
            return



        duration = MovementTime.calculate(
            piece,
            source,
            target
        )


        move = Move(
            piece,
            source,
            target,
            self._arbiter.get_time(),
            duration
        )


        self._arbiter.add_move(move)



    def wait(self, ms):

        self._arbiter.wait(ms)



def get_snapshot(self):

    return self._state.snapshot()
