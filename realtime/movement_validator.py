class MovementValidator:


    # בודק אם כלי במיקום נתון נמצא כרגע בתנועה
    @staticmethod
    def is_moving(
        active_moves,
        position
    ):

        for move in active_moves:

            if move.source == position:
                return True

        return False