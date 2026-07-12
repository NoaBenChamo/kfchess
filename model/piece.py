class Piece:

    def __init__(self, color, piece_type):

        self.color = color
        self.type = piece_type


    def __str__(self):

        return self.color + self.type


    def __repr__(self):

        return f"Piece({self.color}, {self.type})"