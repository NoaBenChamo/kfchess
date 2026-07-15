from model.position import Position

class BoardMapper:

    CELL_WIDTH = 100
    CELL_HEIGHT = 100

    # מאתחל את גודל המשבצת לפי גודל תמונת הלוח
    @staticmethod
    def init(cell_width, cell_height):
        BoardMapper.CELL_WIDTH = cell_width
        BoardMapper.CELL_HEIGHT = cell_height

    # ממיר קואורדינטות מסך למיקום בלוח
    @staticmethod
    def to_position(x, y):
        return Position(
            y // BoardMapper.CELL_HEIGHT,
            x // BoardMapper.CELL_WIDTH
        )

    # ממיר מיקום בלוח לקואורדינטות מסך
    @staticmethod
    def to_pixels(position):
        return (
            position.col * BoardMapper.CELL_WIDTH,
            position.row * BoardMapper.CELL_HEIGHT
        )
