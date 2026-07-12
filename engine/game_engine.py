from model.position import Position

from realtime.move import Move
from realtime.movement_time import MovementTime
from realtime.real_time_arbiter import RealTimeArbiter

from rules.rule_engine import RuleEngine


class GameEngine:


    def __init__(self, board):

        self._board = board

        self._rule_engine = RuleEngine()

        self._arbiter = RealTimeArbiter(
            board
        )

        self._selected = None

        self._game_over = False



    def select(self, position):

        if self._game_over:
            return


        if not self._board.is_inside(position):
            return


        piece = self._board.get(position)


        if piece is None:
            return


        self._selected = position



    def move_request(self, target):

        if self._selected is None:
            return


        source = self._selected


        piece = self._board.get(source)


        if piece is None:
            self._selected = None
            return



        if not self._rule_engine.is_valid_move(
            piece,
            source,
            target,
            self._board
        ):
            self._selected = None
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


        self._selected = None

    def wait(self, ms):

        self._arbiter.wait(ms)


        events = self._arbiter.get_events()


        for event in events:

            if event == "GAME_OVER":
                self._game_over = True



    def get_board(self):

        return self._board



    def is_game_over(self):

        return self._game_over



    def get_selected(self):

        return self._selected



    def set_game_over(self):

        self._game_over = True

    def jump(self, x, y):

        row = y // 100
        col = x // 100

        position = Position(
            row,
            col
        )

        # כרגע רק מעביר הלאה
        # הלוגיקה תישאר ב-Arbiter