class MovementValidator:

    @staticmethod
    def is_moving(active_moves, position):
        for move in active_moves:
            if move.source == position:
                return True
        return False
