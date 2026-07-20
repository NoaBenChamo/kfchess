from model.position import Position
from realtime.jump import Jump
from realtime.move import Move
from realtime.movement_time import MovementTime
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from config.constants import JUMP_DURATION, SHORT_REST_DURATION, LONG_REST_DURATION
from snapshots.game_snapshot import GameSnapshot
from snapshots.piece_snapshot import PieceSnapshot
from snapshots.move_record import MoveRecord
from model.piece_state import PieceState
from bus.event_bus import EventBus
from bus.events import GameStartedEvent, GameOverEvent

class GameEngine:


    def __init__(self, board, event_bus=None):

        self._board = board
        self._rule_engine = RuleEngine()
        self._arbiter = RealTimeArbiter(board)
        self._selected = None
        self._game_over = False
        self._white_moves = []
        self._black_moves = []
        self._bus = event_bus if event_bus is not None else EventBus()

    @property
    def bus(self):
        return self._bus

    def subscribe(self, event_type, handler):
        self._bus.subscribe(event_type, handler)

    def start_game(self):
        self._bus.publish(GameStartedEvent())


    def select(self, position):

        if self._game_over:
            return

        if not self._board.is_inside(position):
            return

        piece = self._board.get(position)

        if piece is None:
            return

        if self._arbiter.is_piece_moving(position):
            return

        if piece.state in (PieceState.SHORT_REST, PieceState.LONG_REST):
            return

        self._selected = position


    def clear_selection(self):
        self._selected = None

    def move_from_to(self, source, target):
        """Atomic board move for network / scripted clients."""
        self.select(source)
        if self._selected != source:
            return False
        return self.move_request(target)

    def move_request(self, target):

        if self._selected is None:
            return False

        source = self._selected
        piece = self._board.get(source)

        if piece is None:
            self._selected = None
            return False

        if self._arbiter.is_piece_moving(source):
            self._selected = None
            return False

        duration = MovementTime.calculate(piece, source, target)
        current_time = self._arbiter.get_time()
        active_moves = self._arbiter.get_active_moves()

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
            return False

        move = Move(
            piece,
            source,
            target,
            current_time,
            duration
        )

        target_piece = self._board.get(target)
        move_type = "capture" if target_piece is not None else "move"

        record = MoveRecord(
            piece.color,
            piece.type,
            source,
            target,
            move_type,
            time_ms=self._arbiter.get_time(),
        )
        if piece.color.lower() == "w":
            self._white_moves.append(record)
        else:
            self._black_moves.append(record)

        self._arbiter.add_move(move)
        self._selected = None
        return True


    def tick(self, ms):

        self._arbiter.tick(ms)
        events = self._arbiter.get_events()

        for event in events:
            if event == "GAME_OVER":
                self._apply_game_over()

    def wait(self, ms):
        """Backward-compatible alias for tick()."""
        self.tick(ms)

    def get_board(self):
        return self._board


    def is_game_over(self):
        return self._game_over


    def get_selected(self):
        return self._selected


    def set_game_over(self):
        self._apply_game_over()

    def _apply_game_over(self):
        if self._game_over:
            return
        self._game_over = True
        self._bus.publish(GameOverEvent(
            timestamp_ms=self._arbiter.get_time(),
        ))


    def create_snapshot(self):

        pieces = []
        current_time = self._arbiter.get_time()
        active_moves = self._arbiter.get_active_moves()
        active_jumps = self._arbiter.get_active_jumps()
        moving_sources = {m.source for m in active_moves}
        jumping_positions = {j.position for j in active_jumps}

        rows = self._board.get_rows()

        for row_idx, row in enumerate(rows):
            for col_idx, piece in enumerate(row):
                if piece is not None:
                    pos = Position(row_idx, col_idx)
                    if pos not in moving_sources:
                        rest_progress = None
                        if piece.state == PieceState.SHORT_REST:
                            rest_progress = 1.0 - (piece.rest_until - current_time) / SHORT_REST_DURATION
                        elif piece.state == PieceState.LONG_REST:
                            rest_progress = 1.0 - (piece.rest_until - current_time) / LONG_REST_DURATION
                        rest_progress = max(0.0, min(1.0, rest_progress)) if rest_progress is not None else None
                        pieces.append(PieceSnapshot(
                            piece.color,
                            piece.type,
                            pos,
                            piece.state,
                            rest_progress=rest_progress
                        ))

        for move in active_moves:
            pieces.append(PieceSnapshot(
                move.piece.color,
                move.piece.type,
                move.source,
                PieceState.MOVE,
                target=move.target,
                progress=move.progress_at(current_time),
            ))

        for jump in active_jumps:
            pieces.append(PieceSnapshot(
                jump.piece.color,
                jump.piece.type,
                jump.position,
                PieceState.JUMP,
                progress=jump.progress_at(current_time),
            ))

        white_score = sum(
            1 for move in self._white_moves if move.move_type == "capture"
        )
        black_score = sum(
            1 for move in self._black_moves if move.move_type == "capture"
        )

        return GameSnapshot(
            board_width=len(rows[0]) if rows else 0,
            board_height=len(rows),
            pieces=pieces,
            selected_cell=self._selected,
            game_over=self._game_over,
            white_moves=list(self._white_moves),
            black_moves=list(self._black_moves),
            white_score=white_score,
            black_score=black_score,
        )


    def jump(self, position):

        if position is None or not self._board.is_inside(position):
            return

        piece = self._board.get(position)

        if piece is None:
            return

        if self._arbiter.is_piece_moving(position):
            return

        self._board.set(position, None)

        jump = Jump(
            position,
            piece,
            self._arbiter.get_time(),
            JUMP_DURATION
        )

        jump_record = MoveRecord(
            piece.color,
            piece.type,
            position,
            position,
            "jump",
            time_ms=self._arbiter.get_time(),
        )
        if piece.color == "w":
            self._white_moves.append(jump_record)
        else:
            self._black_moves.append(jump_record)

        self._arbiter.add_jump(jump)
        self.clear_selection()
