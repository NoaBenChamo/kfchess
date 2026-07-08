class Move:

    def __init__(self, piece, source, target, start_time, duration):
        self.piece = piece
        self.source = source
        self.target = target
        self.arrival_time = start_time + duration


    def is_finished(self, current_time):
        return current_time >= self.arrival_time


    def contains_piece(self, position):
        return self.source == position