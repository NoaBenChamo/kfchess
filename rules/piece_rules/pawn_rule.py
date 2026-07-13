from model.position import Position
from rules.piece_rules.movement_rule import MovementRule

#חוקיות ההזזה של החייל
class PawnRule(MovementRule):

    # בודק אם הרגלי יכול לזוז קדימה, שני צעדים מההתחלה, או לאכול באלכסון
    def can_move(
        self,
        piece,
        source,
        target,
        board,
        active_moves=None,
        move_start_time=None,
        move_duration=None
    ):

        direction = -1 if piece.color == "w" else 1

        row = target.row - source.row
        col = target.col - source.col

        num_rows = len(board.get_rows())

        # צעד רגיל קדימה — התא חייב להיות ריק
        if col == 0 and row == direction:
            return board.get(target) is None

        # שני צעדים משורת ההתחלה — גם התא הביניים חייב להיות ריק
        if col == 0 and row == 2 * direction:

            if piece.color == "w":
                start_row = num_rows - 2
            else:
                start_row = 1

            if source.row != start_row:
                return False

            middle = source.row + direction

            return (
                board.get(target) is None
                and
                board.get(Position(middle, source.col)) is None
            )

        # אכילה באלכסון — חייב להיות כלי אויב ביעד
        if abs(col) == 1 and row == direction:

            target_piece = board.get(target)

            return (
                target_piece is not None
                and
                target_piece.color != piece.color
            )

        return False
