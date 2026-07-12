class Renderer:


    def render(self, snapshot):

        board = snapshot.get_board()

        for row in board.get_rows():

            print(
                " ".join(row)
            )