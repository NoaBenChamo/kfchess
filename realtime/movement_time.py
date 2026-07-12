from config.constants import PIECE_SPEED


class MovementTime:


    @staticmethod
    def calculate(
        piece,
        source,
        target
    ):

        distance = max(
            abs(target.row - source.row),
            abs(target.col - source.col)
        )

        return (
            distance *
            PIECE_SPEED[piece.type]
        )