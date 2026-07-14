class Jump:

    def __init__(
        self,
        position,
        piece,
        start_time,
        duration=1000
    ):

        self.position = position
        self.piece = piece

        self.start_time = start_time
        self.duration = duration

        self.arrival_time = (
            start_time + duration
        )

        # כלי אויב שנלכד בזמן הקפיצה
        self.captured_piece = None


    # בודק אם הקפיצה הסתיימה
    def is_finished(self, current_time):

        return current_time >= self.arrival_time