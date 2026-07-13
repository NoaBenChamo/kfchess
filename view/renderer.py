class Renderer:


    # מצייר את מצב המשחק הנוכחי על המסך
    def render(self, snapshot):

        board = snapshot.get_board()

        for row in board.get_rows():

            print(
                " ".join(row)
            )