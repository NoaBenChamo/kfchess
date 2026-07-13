from model.position import Position


class PathChecker:

    # בודק האם כל המשבצות שבין המקור ליעד פנויות
    # כולל התחשבות בכלים שנמצאים כרגע בתנועה (אם סופק מידע דינמי)
    @staticmethod
    def clear(
        board,
        source,
        target,
        active_moves=None,
        move_start_time=None,
        move_duration=None
    ):

        row_step = PathChecker.step(target.row - source.row)
        col_step = PathChecker.step(target.col - source.col)

        total_distance = max(
            abs(target.row - source.row),
            abs(target.col - source.col)
        )

        # האם יש לבצע גם בדיקת חסימות של כלים שנמצאים בתנועה
        dynamic_check = (
            active_moves is not None
            and move_start_time is not None
            and move_duration is not None
            and total_distance > 0
        )

        current_row = source.row + row_step
        current_col = source.col + col_step
        step_index = 1

        # בודק את כל המשבצות שבין המקור ליעד (לא כולל היעד)
        while (current_row, current_col) != (target.row, target.col):

            current_position = Position(current_row, current_col)

            # הנתיב חסום על ידי כלי שנמצא על הלוח
            if board.get(current_position) is not None:
                return False

            # הנתיב חסום על ידי כלי שיעבור במשבצת באותו זמן
            if dynamic_check:

                passage_time = int(
                    move_start_time
                    + step_index / total_distance * move_duration
                )

                for move in active_moves:
                    if move.position_at(passage_time) == current_position:
                        return False

            current_row += row_step
            current_col += col_step
            step_index += 1

        return True

    # מחזיר את המשבצת הפנויה האחרונה לפני משבצת חסומה
    @staticmethod
    def find_last_free_cell(
        source,
        blocked_cell,
        board,
        active_moves=None,
        arrival_time=None
    ):

        row_step = PathChecker.step(blocked_cell.row - source.row)
        col_step = PathChecker.step(blocked_cell.col - source.col)

        path = []

        current_row = source.row + row_step
        current_col = source.col + col_step

        # בניית כל המשבצות שבין המקור למשבצת החסומה
        while (current_row, current_col) != (
            blocked_cell.row,
            blocked_cell.col
        ):

            path.append(Position(current_row, current_col))

            current_row += row_step
            current_col += col_step

        # מחפש מהסוף להתחלה את המשבצת הפנויה הקרובה ביותר לחסימה
        for cell in reversed(path):

            # המשבצת תפוסה על ידי כלי שנמצא על הלוח
            if board.get(cell) is not None:
                continue

            occupied_by_move = False

            # המשבצת עתידה להיות תפוסה על ידי כלי אחר
            if active_moves is not None and arrival_time is not None:

                for move in active_moves:

                    if (
                        move.target == cell
                        and move.arrival_time <= arrival_time
                    ):
                        occupied_by_move = True
                        break

            if not occupied_by_move:
                return cell

        return None

    # מחזיר את כיוון ההתקדמות:
    # 1  - קדימה
    # -1 - אחורה
    # 0  - ללא שינוי
    @staticmethod
    def step(value):

        if value > 0:
            return 1

        if value < 0:
            return -1

        return 0