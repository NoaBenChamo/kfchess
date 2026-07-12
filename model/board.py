class Board:

    def __init__(self, cells):
        self._cells = cells


    def get_rows(self):
        return self._cells


    def get(self, position):

        return self._cells[
            position.row
        ][
            position.col
        ]


    def set(self, position, value):

        self._cells[
            position.row
        ][
            position.col
        ] = value


    def is_inside(self, position):

        return (
            0 <= position.row < len(self._cells)
            and
            0 <= position.col < len(self._cells[0])
        )


    def __str__(self):

        result = []

        for row in self._cells:

            result.append(
                " ".join(
                    "." if piece is None else str(piece)
                    for piece in row
                )
            )

        return "\n".join(result)