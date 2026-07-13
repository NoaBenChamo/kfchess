class BoardPrinter:


    # מדפיס את הלוח לפלט טקסטואלי עם נקודה לתא ריווח בין כלים
    @staticmethod
    def print(board):

        for row in board.get_rows():

            print(
                " ".join(
                    "."
                    if piece is None
                    else str(piece)
                    for piece in row
                )
            )