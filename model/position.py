#מייצג את המיקום של ריבוע בלוח המשחק לפי שורה ועמודה 
class Position:

    def __init__(self, row, col):
        self.row = row
        self.col = col


    # בודק שוויון בין שתי מקומות לפי שורה ועמודה
    def __eq__(self, other):
        return (
            isinstance(other, Position)
            and self.row == other.row
            and self.col == other.col
        )


    # מחזיר ערך גיבוב למיקום כדי שיוכל לשמש כמפתח במילון
    def __hash__(self):
        return hash((self.row, self.col))


    # מחזיר ייצוג מפורט של המיקום לצורך דיבאג
    def __repr__(self):
        return f"Position({self.row}, {self.col})"