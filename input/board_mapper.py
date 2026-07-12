class BoardMapper:

    CELL_SIZE = 100


    @staticmethod
    def to_position(x, y):

        return (
            y // BoardMapper.CELL_SIZE,
            x // BoardMapper.CELL_SIZE
        )