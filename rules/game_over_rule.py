class GameOverRule:

    @staticmethod
    def is_king_captured(target_piece):
        return target_piece[1] == "K"
