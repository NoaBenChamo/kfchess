from realtime.clock import GameClock
from realtime.crossing_detector import CrossingDetector
from realtime.movement_validator import MovementValidator
from rules.capture_rule import CaptureRule
from rules.game_over_rule import GameOverRule
from rules.path_checker import PathChecker
from rules.promotion_rule import PromotionRule

# TODO:
# לטפל במקרה שבו כלי מסיים תנועה בדיוק למשבצת שאליה נוחת כלי שנמצא באוויר (Jump).
# יש להגדיר בצורה אחידה מה קורה לכלי הנכנס (אכילה/ביטול התנועה/ניקוי המקור)
# תוך שמירה על מצב עקבי של הלוח ושל רשימת התנועות הפעילות.
class RealTimeArbiter:


    def __init__(self, board):

        self._board = board
        self._clock = GameClock()
        self._active_moves = []
        self._active_jumps = []
        self._game_events = []
        self._landed_via_move = {}  


    # מוסיף תנועה פעילה לרשימת התנועות
    def add_move(self, move):
        self._active_moves.append(move)


    # מוסיף קפיצה פעילה לרשימת הקפיצות
    def add_jump(self, jump):
        self._active_jumps.append(jump)


    # מקדם זמן ומעבד אירועים שהסתיימו
    def tick(self, ms):

        self._clock.advance(ms)

        # קודם מסיימים תנועות רגילות
        self.resolve_finished_moves()

        # אחר כך מחזירים קפיצות
        self.resolve_finished_jumps()


    # מחזיר את הזמן הנוכחי של השעון
    def get_time(self):
        return self._clock.get_time()


    # בודק אם כלי במיקום נתון נמצא כרגע בתנועה
    def is_moving(self, position):

        return MovementValidator.is_moving(
            self._active_moves,
            position
        )


    # מנחית תנועה אחת על הלוח תוך טיפול בהתנגשויות
    def resolve_single_arrival(self, move):

        # בדיקה האם יש כלי שנמצא בקפיצה באותה משבצת
        airborne_jump = self._find_jump_at(move.target)

        if airborne_jump is not None:

            # כלי מאותו צבע חוסם את הנחיתה
            if airborne_jump.piece.color == move.piece.color:
                return

            # כלי שנע מגיע לכלי שבאוויר:
            # הכלי שבאוויר נשאר, והכלי הנכנס נלכד
            airborne_jump.captured_piece = move.piece

            return


        target_piece = self._board.get(move.target)

        # תא ריק — נחיתה רגילה
        if target_piece is None:
            self.finish_move_at(move, move.target)
            return


        # כלי ידיד ביעד — עצירה לפני התא החסום
        if target_piece.color == move.piece.color:

            stop_cell = PathChecker.find_last_free_cell(
                move.source,
                move.target,
                self._board,
                self._active_moves,
                move.arrival_time
            )

            if stop_cell is not None:
                self.finish_move_at(move, stop_cell)

            return


        # כלי אויב ביעד — אכילה
        self.finish_move_at(move, move.target)



    # מנחית כלי במיקום סופי ומעדכן את הלוח בהתאם
    def finish_move_at(self, move, position):

        target_piece = self._board.get(position)

        # בדיקת אכילה סופית
        if target_piece is not None:
            if not CaptureRule.can_capture(move.piece, target_piece):
                return

        # ניקוי תא המקור רק אם אין תנועה אחרת שיוצאת מאותה תא
        other_uses_source = any(
            m for m in self._active_moves
            if m is not move and m.source == move.source
        )

        if not other_uses_source:
            self._board.set(move.source, None)

        # נחיתת הכלי במיקום היעד
        self._board.set(position, move.piece)

        # רישום נחיתה לצורך טיפול בקפיצות
        self._landed_via_move[position] = move.source

        # בדיקת קידום רגלי
        if PromotionRule.should_promote(move.piece, position, self._board):
            move.piece.type = "Q"

        # בדיקה אם נלכד מלך
        if GameOverRule.is_king_captured(target_piece):
            self._game_events.append("GAME_OVER")


    # מעבד קפיצות שהסתיימו ומחזיר את הכלי ללוח
    def resolve_finished_jumps(self):

        current_time = self._clock.get_time()

        # איסוף כל הקפיצות שהסתיימו
        finished = [
            jump for jump in self._active_jumps
            if jump.is_finished(current_time)
        ]

        # נחיתת כל קפיצה והסרתה מהרשימה
        for jump in finished:
            self._land_jump(jump)
            self._active_jumps.remove(jump)


    # מנחית כלי קופץ בחזרה למקומו ומטפל בהתנגשויות
    def _land_jump(self, jump):

        if jump.captured_piece is not None:

            # הכלי שניסה להגיע נלכד,
            # אבל הכלי שקפץ חוזר ללוח
            self._board.set(
                jump.position,
                jump.piece
            )

            return  

        piece_on_square = self._board.get(jump.position)

        # תא ריק — נחיתה רגילה
        if piece_on_square is None:
            self._board.set(jump.position, jump.piece)
            return

        # כלי ידיד הגיע בזמן הקפיצה — דוחפים אותו אחור
        if piece_on_square.color == jump.piece.color:

            friendly_move = self._find_move_at(jump.position)

            if friendly_move is not None:
                stop = PathChecker.find_last_free_cell(
                    friendly_move.source,
                    jump.position,
                    self._board,
                    self._active_moves,
                    friendly_move.arrival_time
                )

                if stop is not None:
                    self._board.set(stop, piece_on_square)

            # פינוי התא ונחיתת הקופץ
            self._board.set(jump.position, None)
            self._board.set(jump.position, jump.piece)
            return

        # כלי אויב בתא — אכילה
        self._board.set(jump.position, jump.piece)

        if GameOverRule.is_king_captured(piece_on_square):
            self._game_events.append("GAME_OVER")


    # מחזיר את האירועים שנצברו ומנקה את הרשימה
    def get_events(self):

        events = self._game_events[:]
        self._game_events.clear()
        return events


    # בודק אם כלי במיקום נתון נמצא כרגע בתנועה פעילה
    def is_piece_moving(self, position):

        for move in self._active_moves:
            if move.source == position:
                return True

        return False


    # מחזיר עותק של רשימת התנועות הפעילות
    def get_active_moves(self):
        return list(self._active_moves)


    # בודק אם כלי נחת במיקום זה בעקבות תנועה
    def was_landed_via_move(self, position):
        return position in self._landed_via_move


    # מחזיר את מיקום המקור של התנועה שנחתה במיקום זה
    def get_landing_source(self, position):
        return self._landed_via_move.get(position)


    # מחזיר את התנועה הפעילה שיעדה למיקום זה, או None
    def _find_move_at(self, position):
        for move in self._active_moves:
            if move.target == position:
                return move
        return None


    def _find_jump_at(self, position):

        for jump in self._active_jumps:
            if jump.position == position:
                return jump

        return None
    

    # מסיים את כל התנועות שהגיעו ליעד
    def resolve_finished_moves(self):

        current_time = self._clock.get_time()

        finished_moves = [
            move
            for move in self._active_moves
            if move.is_finished(current_time)
        ]

        for move in finished_moves:

            self.resolve_single_arrival(move)

            if move in self._active_moves:
                self._active_moves.remove(move)