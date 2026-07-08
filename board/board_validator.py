from config.constants import EMPTY, VALID_COLORS, VALID_PIECES


class BoardValidator:

    @staticmethod
    def validate(board):

        rows = board.get_rows()

        if not rows:
            return "ERROR INVALID_BOARD"

        size = len(rows[0])

        for row in rows:

            if len(row) != size:
                return "ERROR ROW_WIDTH_MISMATCH"
            for token in row:

                if not BoardValidator.valid_token(token):
                    return "ERROR UNKNOWN_TOKEN"

        return None


    @staticmethod
    def valid_token(token):

        if token == EMPTY:
            return True

        if len(token) != 2:
            return False

        return (
            token[0] in VALID_COLORS
            and
            token[1] in VALID_PIECES
        )