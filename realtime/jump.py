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

        self.end_time = (
            start_time + duration
        )


    def is_finished(self, current_time):

        return current_time >= self.end_time