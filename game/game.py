from game.clock import GameClock
from movement.rule_factory import RuleFactory
from rules.capture_rule import CaptureRule
from movement.move import Move
from game.movement_time import MovementTime 
from movement.movement_validator import MovementValidator
from rules.game_over_rule import GameOverRule
from rules.promotion_rule import PromotionRule


class Game:

    def __init__(self, board):
        self._board = board
        self._clock = GameClock()
        self._selected = None
        self._active_moves = []
        self._game_over = False



    def click(self, x, y):
        if self._game_over:
            return
        row = y // 100
        col = x // 100

        if not self._board.is_inside(row, col):
            return


        cell = self._board.get(row, col)

        if MovementValidator.is_moving(self._active_moves, (row, col)):
            return

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
            if move.contains_piece(source):
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

        duration = MovementTime.calculate(
            piece,
            source,
            target
        )

        move = Move(
            piece,
            source,
            target,
            self._clock.get_time(),
            duration
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
                target_piece = self._board.get(
                    move.target[0],
                    move.target[1]
                )


                if not CaptureRule.can_capture(
                    move.piece,
                    target_piece
                ):
                    finished_moves.append(move)
                    continue

                self._board.set(
                    move.target[0],
                    move.target[1],
                    move.piece
                )
                if PromotionRule.should_promote(move.piece, move.target, self._board):
                    self._board.set(move.target[0], move.target[1], move.piece[0] + "Q")

                if GameOverRule.is_king_captured(target_piece):
                    self._game_over = True

                finished_moves.append(move)



        for move in finished_moves:
            self._active_moves.remove(move)



    def get_board(self):

        return self._board

    def resolve_conflicts(self, moves):

        result = []

        occupied_targets = set()


        for move in moves:

            if move.target in occupied_targets:
                continue

            occupied_targets.add(move.target)
            result.append(move)


        return result