class GameOverRule:


    # בודק אם הכלי שנלכד הוא מלך
    @staticmethod
    def is_king_captured(piece):

        return (
            piece is not None
            and
            piece.type == "K"
        )