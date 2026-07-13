from model.position import Position

class BoardMapper:

    CELL_SIZE = 100

    # ממיר קואורדינטות מסך למיקום בלוח
    @staticmethod
    def to_position(x, y):

        return Position(
            y // BoardMapper.CELL_SIZE,
            x // BoardMapper.CELL_SIZE
        )