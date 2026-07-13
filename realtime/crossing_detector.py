from rules.path_checker import PathChecker


class CrossingDetector:

    # מזהה התנגשויות בין שני כלים מאותו צבע שנמצאים בתנועה.
    # הכלי שמפסיד נעצר לפני נקודת ההתנגשות או מבוטל אם אין מקום לעצור.
    @staticmethod
    def detect_and_resolve(active_moves, board):

        cancelled = []

        # עותק של רשימת המהלכים כדי שניתן יהיה לעדכן את המקור
        moves_snapshot = list(active_moves)

        # מהלכים שכבר קוצרו
        already_shortened = set()

        for i, move_a in enumerate(moves_snapshot):

            if move_a in already_shortened:
                continue

            for move_b in moves_snapshot[i + 1:]:

                if move_b in already_shortened:
                    continue

                # מטפל רק בכלים מאותו צבע
                if move_a.piece.color != move_b.piece.color:
                    continue

                # מחפש נקודת התנגשות
                crossing = CrossingDetector._find_crossing(
                    move_a,
                    move_b
                )

                if crossing is None:
                    continue

                crossing_cell, t_a, t_b = crossing

                # הכלי שמגיע מאוחר יותר מפסיד
                if (
                    t_a > t_b
                    or
                    (t_a == t_b and move_a.move_id > move_b.move_id)
                ):
                    loser = move_a
                else:
                    loser = move_b

                # מחפש את המשבצת הפנויה האחרונה לפני ההתנגשות
                stop_cell = PathChecker.find_last_free_cell(
                    loser.source,
                    crossing_cell,
                    board,
                    active_moves,
                    loser.time_at(crossing_cell)
                )

                already_shortened.add(loser)

                # אין מקום לעצור - מבטל את המהלך
                if stop_cell is None:
                    active_moves.remove(loser)
                    cancelled.append(loser)

                # אחרת מקצר את המהלך
                else:
                    CrossingDetector._shorten_move(
                        loser,
                        stop_cell
                    )

        return cancelled

    # מחפש משבצת שבה שני המהלכים נמצאים באותו זמן
    @staticmethod
    def _find_crossing(move_a, move_b):

        for cell in move_a.get_path():

            t_a = move_a.time_at(cell)

            if t_a is None:
                continue

            t_b = move_b.time_at(cell)

            if t_b is None:
                continue

            if t_a == t_b:
                return (cell, t_a, t_b)

        return None

    # מקצר את המהלך עד למשבצת החדשה
    @staticmethod
    def _shorten_move(move, stop_cell):

        original_time_at_stop = move.time_at(stop_cell)

        # יעד חדש
        move.target = stop_cell

        # זמן ההגעה החדש
        if original_time_at_stop is not None:
            move.arrival_time = original_time_at_stop

        # חישוב חלופי אם אין זמן מדויק
        else:

            path = move.get_path()

            if stop_cell in path:

                idx = path.index(stop_cell)
                total = len(path)

                move.arrival_time = int(
                    move.start_time
                    + (idx + 1) / total * move.duration
                )