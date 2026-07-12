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



    def click(self, x, y):

        if self._state.is_game_over():
            return


        row = y // 100
        col = x // 100


        board = self._state.get_board()


        if not board.is_inside(row, col):
            return


        position = (row, col)


        if self._arbiter.is_moving(position):
            return


        if self._arbiter.is_jumping(position):
            return


        cell = board.get(row, col)


        selected = self._state.get_selected()


        if selected is None:

            if cell != ".":
                self._state.set_selected(position)

            return



        selected_piece = board.get(
            selected[0],
            selected[1]
        )


        if (
            cell != "."
            and
            cell[0] == selected_piece[0]
        ):

            self._state.set_selected(position)
            return



        self.move_request(
            selected,
            position
        )


        self._state.set_selected(None)



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



    def get_board(self):

        return self._state.get_board()



    def selected_piece(self):

        return self._state.get_selected()