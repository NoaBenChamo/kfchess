class Board:

    def __init__(self, cells):
        self._cells = cells


    def get_rows(self):
        return self._cells


    def get(self, row, col):
        return self._cells[row][col]


    def set(self, row, col, value):
        self._cells[row][col] = value


    def is_inside(self, row, col):

        return (
            0 <= row < len(self._cells)
            and
            0 <= col < len(self._cells[0])
        )