class BoardPrinter:

    @staticmethod
    def print(board):

        for row in board.get_rows():
            print(" ".join(row))