class CaptureRule:


    @staticmethod
    def can_capture(source_piece, target_piece):

        if target_piece is None:
            return True


        return (
            source_piece.color
            !=
            target_piece.color
        )