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


    # מחזיר את ה-offset האנכי בפיקסלים לפי הזמן (קשת קפיצה)
    def y_offset_at(self, current_time, jump_height=40):
        t = max(0.0, min(1.0, (current_time - self.start_time) / self.duration))
        return -int(jump_height * 4 * t * (1 - t))

    # בודק אם הקפיצה הסתיימה
    def is_finished(self, current_time):

        return current_time >= self.arrival_time