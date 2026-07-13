#מייצג את הלוח של המשחק כרשימת רשימות של כלים
class Board:

    def __init__(self, cells):
        self._cells = cells


    # מחזיר את כל השורות של הלוח כרשימת רשימות
    def get_rows(self):
        return self._cells


    # מחזיר את הכלי הנמצא במיקום הנתון
    def get(self, position):

        return self._cells[
            position.row
        ][
            position.col
        ]


    # מעדכן את התא במיקום הנתון לערך חדש
    def set(self, position, value):

        self._cells[
            position.row
        ][
            position.col
        ] = value


    # בודק אם המיקום נמצא בתחום הלוח
    def is_inside(self, position):

        return (
            0 <= position.row < len(self._cells)
            and
            0 <= position.col < len(self._cells[0])
        )


    # מחזיר ייצוג טקסטואלי של הלוח כמחרוזת שורות
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