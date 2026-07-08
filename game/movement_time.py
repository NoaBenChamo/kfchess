from config.constants import PIECE_SPEED


class MovementTime:

    @staticmethod
    def calculate(piece, source, target):

        distance = max(
            abs(target[0] - source[0]),
            abs(target[1] - source[1])
        )

        return distance * PIECE_SPEED[piece[1]]