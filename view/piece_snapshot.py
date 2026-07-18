#the object that the view get from the backend
class PieceSnapshot:

    def __init__(self, color, piece_type, position, state, pixel_x=None, pixel_y=None, rest_progress=None):
        self.color = color
        self.piece_type = piece_type
        self.position = position
        self.state = state
        self.pixel_x = pixel_x
        self.pixel_y = pixel_y
        self.rest_progress = rest_progress
