class GameOverRule:

    @staticmethod
    def is_king_captured(target_piece):
        return (
            len(target_piece) > 1
            and target_piece[1] == "K"
        )
