class MovementRule:

    # ממשק בסיס שכל כלל תנועה חייב לממש
    def can_move(
        self,
        piece,
        source,
        target,
        board,
        active_moves=None,
        move_start_time=None,
        move_duration=None
    ):
        raise NotImplementedError
