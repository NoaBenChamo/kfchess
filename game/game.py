from game.clock import GameClock
from movement.rule_factory import RuleFactory

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

        # לחיצה על כלי
        if cell != ".":
            self._selected = (row, col)
            return

        # לחיצה על תא ריק בלי בחירה
        if self._selected is None:
            return

        # בקשת תנועה
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


        if not rule.can_move(source, target):
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