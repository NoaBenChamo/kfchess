from kungfu_chess.model.board import Board


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
                cells.append(line.split())

        return Board(cells)
