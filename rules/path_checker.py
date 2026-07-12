from model.position import Position

class PathChecker:

    @staticmethod
    def clear(board, source, target):

        row_step = PathChecker.step(
            target.row - source.row
        )

        col_step = PathChecker.step(
            target.col - source.col
        )

        row = source.row + row_step
        col = source.col + col_step


        while (row, col) != (target.row, target.col):

            if board.get(Position(row, col)) is not None:
                return False

            row += row_step
            col += col_step


        return True


    @staticmethod
    def step(value):

        if value > 0:
            return 1

        if value < 0:
            return -1

        return 0