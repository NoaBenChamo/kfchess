from game.clock import GameClock
from movement.rule_factory import RuleFactory
from rules.capture_rule import CaptureRule

class Game:

    def __init__(self, board):
        self._board = board
        self._clock = GameClock()
        self._selected = None

    def click(self, x, y):

        row = y // 100
        col = x // 100

        if not self._board.is_inside(row, col):
            return

        cell = self._board.get(row, col)

        # אין כלי נבחר עדיין
        if self._selected is None:

            if cell != ".":
                self._selected = (row, col)

            return


        # יש כלי נבחר

        selected_piece = self._board.get(
            self._selected[0],
            self._selected[1]
        )


        # לחיצה על כלי ידידותי - מחליפים בחירה
        if (
            cell != "."
            and
            cell[0] == selected_piece[0]
        ):
            self._selected = (row, col)
            return


        # אחרת מנסים לבצע תנועה
        self.move_request(
            self._selected,
            (row, col)
        )

        self._selected = None


    def move_request(self, source, target):

        piece = self._board.get(
            source[0],
            source[1]
        )

        rule = RuleFactory.get(piece[1])

        if not rule.can_move(
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

        self._board.set(
            source[0],
            source[1],
            "."
        )

        self._board.set(
            target[0],
            target[1],
            piece
        )


    def wait(self, ms):
        self._clock.advance(ms)


    def get_board(self):
        return self._board