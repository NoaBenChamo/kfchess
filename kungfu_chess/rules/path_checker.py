class PathChecker:

    @staticmethod
    def clear(board, source, target):

        row_step = PathChecker.step(
            target[0] - source[0]
        )

        col_step = PathChecker.step(
            target[1] - source[1]
        )

        row = source[0] + row_step
        col = source[1] + col_step


        while (row, col) != target:

            if board.get(row, col) != ".":
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
