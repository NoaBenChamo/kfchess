from model.board import Board
from model.piece import Piece
from config.constants import VALID_COLORS, VALID_PIECES


class BoardParser:


    @staticmethod
    def parse(lines):

        cells = []

        reading = False

        width = None


        for line in lines:

            line = line.strip()


            if line == "Board:":
                reading = True
                continue


            if line == "Commands:":
                break


            if reading and line:

                tokens = line.split()

                if width is None:
                    width = len(tokens)
                elif len(tokens) != width:
                    raise ValueError("ROW_WIDTH_MISMATCH")

                row = []

                for token in tokens:

                    if token == ".":
                        row.append(None)

                    elif len(token) == 2 and token[0] in VALID_COLORS and token[1] in VALID_PIECES:
                        row.append(Piece(token[0], token[1]))

                    else:
                        raise ValueError("UNKNOWN_TOKEN")


                cells.append(row)


        return Board(cells)