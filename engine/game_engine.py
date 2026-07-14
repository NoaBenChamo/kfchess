from model.position import Position
from realtime.jump import Jump
from realtime.move import Move
from realtime.movement_time import MovementTime
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from config.constants import JUMP_DURATION
from input.board_mapper import BoardMapper

#מנהל את המשחק
class GameEngine:


    def __init__(self, board):

        self._board = board
        self._rule_engine = RuleEngine()
        self._arbiter = RealTimeArbiter(board)
        self._selected = None
        self._game_over = False


    # בוחר כלי על הלוח רק במקרה שהבחירה חוקית
    def select(self, position):

        if self._game_over:
            return

        if not self._board.is_inside(position):
            return

        piece = self._board.get(position)

        if piece is None:
            return

        # אין בחירה של כלי בתנועה
        if self._arbiter.is_piece_moving(position):
            return

        self._selected = position


    # מנקה את הבחירה הנוכחית 
    def clear_selection(self):
        self._selected = None


    # מקבל בקשת הזזה, מאמת את החוקיות ומוסיף תנועה פעילה אם התנועה חוקית
    def move_request(self, target):

        # אין בקשה בלי בחירה
        if self._selected is None:
            return

        source = self._selected
        piece = self._board.get(source)

        # הכלי כבר נעלם מהלוח
        if piece is None:
            self._selected = None
            return

        # הכלי כבר בתנועה
        if self._arbiter.is_piece_moving(source):
            self._selected = None
            return

        # חישוב זמן התנועה
        duration = MovementTime.calculate(piece, source, target)
        current_time = self._arbiter.get_time()
        active_moves = self._arbiter.get_active_moves()

        # אימות חוקייות ההזזה
        if not self._rule_engine.is_valid_move(
            piece,
            source,
            target,
            self._board,
            active_moves,
            current_time,
            duration
        ):
            self._selected = None
            return

        # יצירת התנועה והוספתה לרשימת התנועות הפעילות
        move = Move(
            piece,
            source,
            target,
            current_time,
            duration
        )

        self._arbiter.add_move(move)
        self._selected = None


    # מקדם את השעון ב-ms ומעבד את האירועים שנוצרו באותה תקופה
    def wait(self, ms):

        self._arbiter.wait(ms)
        events = self._arbiter.get_events()

        # בדיקה אם אחד האירועים הוא סיום משחק
        for event in events:
            if event == "GAME_OVER":
                self._game_over = True


    # מחזיר את הלוח הנוכחי
    def get_board(self):
        return self._board


    # מחזיר אם המשחק הסתיים
    def is_game_over(self):
        return self._game_over


    # מחזיר את המיקום הנבחר כרגע
    def get_selected(self):
        return self._selected


    # מסמן את המשחק כהסתיים מבחוץ
    def set_game_over(self):
        self._game_over = True


    # מרים כלי מהלוח זמנית ורושם קפיצה שתנחת אחרי JUMP_DURATION מילישניות
    def jump(self, x, y):

        position = BoardMapper.to_position(x, y)

        # בדיקה שהמיקום נמצא בתוך הלוח
        if not self._board.is_inside(position):
            return

        piece = self._board.get(position)

        # אין כלי להרים
        if piece is None:
            return

        # אי אפשר לקפוץ עם כלי שנמצא בתנועה
        if self._arbiter.is_piece_moving(position):
            return

        # לא ניתן לקפוץ עם כלי שנחת עכשיו מתנועה
        if self._arbiter.was_landed_via_move(position):
            return

        # הסרת הכלי מהלוח ויצירת קפיצה
        self._board.set(position, None)

        jump = Jump(
            position,
            piece,
            self._arbiter.get_time(),
            JUMP_DURATION
        )

        self._arbiter.add_jump(jump)
        self.clear_selection()
