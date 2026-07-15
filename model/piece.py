from view.piece_state import PieceState

#מייצג כלי שחמט עם צבע וסוג
class Piece:

    def __init__(self, color, piece_type):
        self.color = color
        self.type = piece_type
        self.state = PieceState.IDLE


    # מחזיר ייצוג טקסטואלי של הכלי בפורמט צבע+סוג
    def __str__(self):
        return self.color + self.type


    # מחזיר ייצוג מפורט של הכלי לצורך דיבאג
    def __repr__(self):
        return f"Piece({self.color}, {self.type})"