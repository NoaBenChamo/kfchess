class CaptureRule:


    @staticmethod
    def can_capture(source_piece, target_piece):

        if target_piece == ".":
            return True


        return (
            source_piece[0]
            !=
            target_piece[0]
        )