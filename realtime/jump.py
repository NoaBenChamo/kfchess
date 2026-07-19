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


    def progress_at(self, current_time):
        """Return the semantic progress of the jump, from 0.0 to 1.0."""
        return max(0.0, min(1.0, (current_time - self.start_time) / self.duration))

    # בודק אם הקפיצה הסתיימה
    def is_finished(self, current_time):

        return current_time >= self.arrival_time
