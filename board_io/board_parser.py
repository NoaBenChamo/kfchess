from model.board import Board
from model.piece import Piece


class BoardParser:


    @staticmethod
    def parse(lines):

        cells = []

        reading = False


        for line in lines:

            line = line.strip()


            if line == "Board:":
                reading = True
                continue


            if line == "Commands:":
                break


            if reading and line:

                row = []

                for token in line.split():

                    if token == ".":
                        row.append(None)

                    else:
                        row.append(
                            Piece(
                                token[0],
                                token[1]
                            )
                        )


                cells.append(row)


        return Board(cells)