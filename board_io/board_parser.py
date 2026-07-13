from model.board import Board
from model.piece import Piece
from config.constants import VALID_COLORS, VALID_PIECES


class BoardParser:

    # ממיר את שורות הקלט ובונה לוח משחק עם כלים לפי הטוקנים שבקלט
    @staticmethod
    def parse(lines):

        cells = []

        reading = False

        width = None


        for line in lines:

            line = line.strip()

            # זיהוי תחילת הגדרת הלוח
            if line == "Board:":
                reading = True
                continue

            # עצירה כשמגיעים לפקודות
            if line == "Commands:":
                break


            if reading and line:

                tokens = line.split()

                # בדיקת עקביות רוחב השורות
                if width is None:
                    width = len(tokens)
                elif len(tokens) != width:
                    raise ValueError("ROW_WIDTH_MISMATCH")

                row = []

                # המרת כל טוקן לכלי או לתא ריק
                for token in tokens:

                    if token == ".":
                        row.append(None)

                    elif len(token) == 2 and token[0] in VALID_COLORS and token[1] in VALID_PIECES:
                        row.append(Piece(token[0], token[1]))

                    else:
                        raise ValueError("UNKNOWN_TOKEN")


                cells.append(row)


        return Board(cells)