class Controller:

    def __init__(self, game_engine, board_mapper):

        self._game_engine = game_engine
        self._board_mapper = board_mapper


    # מעבד לחיצה על הלוח
    def click(self, x, y):

        position = self._board_mapper.to_position(x, y)

        if position is None:
            return

        if self._game_engine.get_selected() is None:
            self._select_piece(position)

        else:
            self._handle_second_click(position)



    # בוחר כלי כאשר אין בחירה קיימת
    def _select_piece(self, position):

        self._game_engine.select(position)



    # מטפל בלחיצה לאחר שכבר נבחר כלי
    def _handle_second_click(self, position):

        piece_at_click = self._game_engine.get_board().get(position)

        selected = self._game_engine.get_selected()

        selected_piece = (
            self._game_engine.get_board().get(selected)
            if selected is not None
            else None
        )

        # כלי מאותו צבע - החלפת הבחירה
        if self._is_friendly_piece(
            piece_at_click,
            selected_piece,
            position,
            selected
        ):
            self._game_engine.clear_selection()
            self._game_engine.select(position)

        # אחרת ניסיון לבצע הזזה
        else:
            self._game_engine.move_request(position)



    # בודק האם הלחיצה היא על כלי ידידותי אחר
    def _is_friendly_piece(
        self,
        clicked_piece,
        selected_piece,
        position,
        selected_position
    ):

        return (
            clicked_piece is not None
            and selected_piece is not None
            and clicked_piece.color == selected_piece.color
            and position != selected_position
        )



    # מקדם את זמן המשחק במספר מילישניות נתון
    def tick(self, ms):

        self._game_engine.tick(ms)



    def wait(self, ms):
        self._game_engine.tick(ms)



    # מחזיר את מצב הלוח הנוכחי
    def get_board(self):

        return self._game_engine.get_board()



    # שולח בקשת קפיצה למנוע המשחק
    def jump(self, x, y):

        position = self._board_mapper.to_position(x, y)

        if position is None:
            return

        self._game_engine.jump(position)
