from game.clock import GameClock
from movement.rule_factory import RuleFactory
from rules.capture_rule import CaptureRule
from movement.move import Move
from config.constants import MOVE_DURATION


class Game:

    def __init__(self, board):
        self._board = board
        self._clock = GameClock()
        self._selected = None
        self._active_moves = []


    def click(self, x, y):

        row = y // 100
        col = x // 100

        if not self._board.is_inside(row, col):
            return


        cell = self._board.get(row, col)


        # אין כלי נבחר
        if self._selected is None:

            if cell != ".":
                self._selected = (row, col)

            return


        selected_piece = self._board.get(
            self._selected[0],
            self._selected[1]
        )


        # בחירת כלי אחר מאותו צבע
        if (
            cell != "."
            and
            cell[0] == selected_piece[0]
        ):
            self._selected = (row, col)
            return


        # ניסיון לבצע תנועה
        self.move_request(
            self._selected,
            (row, col)
        )

        self._selected = None



    def move_request(self, source, target):

        # כלי שנמצא כבר בתנועה לא יכול לקבל פקודה חדשה
        for move in self._active_moves:
            if move.source == source:
                return


        piece = self._board.get(
            source[0],
            source[1]
        )


        if piece == ".":
            return


        rule = RuleFactory.get(piece[1])


        if not rule.can_move(
            piece,
            source,
            target,
            self._board
        ):
            return



        target_piece = self._board.get(
            target[0],
            target[1]
        )


        if not CaptureRule.can_capture(
            piece,
            target_piece
        ):
            return



        move = Move(
            piece,
            source,
            target,
            self._clock.get_time(),
            MOVE_DURATION
        )


        self._active_moves.append(move)



    def wait(self, ms):

        self._clock.advance(ms)

        self.finish_moves()



    def finish_moves(self):

        current_time = self._clock.get_time()

        finished_moves = []


        for move in self._active_moves:

            if move.is_finished(current_time):


                self._board.set(
                    move.source[0],
                    move.source[1],
                    "."
                )


                self._board.set(
                    move.target[0],
                    move.target[1],
                    move.piece
                )


                finished_moves.append(move)



        for move in finished_moves:
            self._active_moves.remove(move)



    def get_board(self):

        return self._board