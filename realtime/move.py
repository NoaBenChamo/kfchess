from model.position import Position

#אוביקט המכיל את כל המידע על תנועה של כלי מהמקור ליעד בזמן נתון
class Move:

    _counter = 0

    def __init__(
        self,
        piece,
        source,
        target,
        start_time,
        duration
    ):

        Move._counter += 1
        self.move_id = Move._counter

        self.piece = piece
        self.source = source
        self.target = target

        self.start_time = start_time
        self.duration = duration

        self.arrival_time = (
            start_time + duration
        )


    # בודק אם התנועה הסתיימה לפי השעון
    def is_finished(self, current_time):
        return current_time >= self.arrival_time

    def progress_at(self, current_time):
        """Return the semantic progress of the move, from 0.0 to 1.0."""
        return max(0.0, min(1.0, (current_time - self.start_time) / self.duration))


    # בודק אם התנועה עוברת דרך המיקום הנתון
    def contains_piece(self, position):
        return self.source == position


    # מחזיר את כל התאים של הנתיב מהמקור עד היעד בסדר
    def get_path(self):

        row_step = _step(self.target.row - self.source.row)
        col_step = _step(self.target.col - self.source.col)

        path = []

        row = self.source.row + row_step
        col = self.source.col + col_step

        # בניית הנתיב תא אחר תא
        while (row, col) != (
            self.target.row,
            self.target.col
        ):
            path.append(Position(row, col))
            row += row_step
            col += col_step

        path.append(Position(self.target.row, self.target.col))

        return path


    # מחזיר את התא הדיסקרטי שהכלי נמצא בו בזמן נתון
    def position_at(self, time):

        # לפני התנועה או אחריה — מיקום קצה
        if time <= self.start_time:
            return self.source

        if time >= self.arrival_time:
            return self.target

        path = self.get_path()
        total_steps = len(path)
        elapsed = time - self.start_time

        # חישוב הצעד הנוכחי בנתיב
        step_index = int(elapsed / self.duration * total_steps)
        step_index = max(0, min(step_index, total_steps - 1))

        return path[step_index]


    # מחזיר את הזמן שבו הכלי נכנס לתא הנתון, או None אם אינו בנתיב
    def time_at(self, position):

        # מיקום המקור — זמן התחלה
        if position == self.source:
            return self.start_time

        path = self.get_path()
        total_steps = len(path)

        # חיפוש התא בנתיב וחישוב זמן הכניסה
        for index, cell in enumerate(path):

            if cell == position:
                return int(
                    self.start_time
                    + (index + 1) / total_steps
                    * self.duration
                )

        return None


def _step(value):

    if value > 0:
        return 1

    if value < 0:
        return -1

    return 0
