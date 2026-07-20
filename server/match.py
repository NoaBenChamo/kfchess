import asyncio
import logging

from board_io.board_parser import BoardParser
from engine.game_engine import GameEngine
from server.opening_board import STANDARD_OPENING
from server.snapshot_serializer import snapshot_to_dict
from shared.protocol import encode_message

logger = logging.getLogger(__name__)


class Match:
    """
    One authoritative networked game: owns GameEngine, sequence, and tick loop.
    """

    def __init__(self, game_id, engine=None):
        self.game_id = game_id
        if engine is None:
            board = BoardParser.parse(STANDARD_OPENING.strip().splitlines())
            engine = GameEngine(board)
            engine.start_game()
        self.engine = engine
        self.sequence = 0
        self.lock = asyncio.Lock()
        self._connections = set()
        self._closed = False
        self._tick_task = None
        self._last_state_key = self._state_key()

    def bump_sequence(self):
        self.sequence += 1
        return self.sequence

    def add_connection(self, websocket):
        self._connections.add(websocket)

    def remove_connection(self, websocket):
        self._connections.discard(websocket)

    async def start_tick_loop(self, tick_ms):
        if self._tick_task is not None:
            return
        self._closed = False
        self._tick_task = asyncio.create_task(
            self._tick_loop(tick_ms),
            name=f"match-tick-{self.game_id}",
        )

    async def stop(self):
        self._closed = True
        task = self._tick_task
        self._tick_task = None
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @property
    def tick_running(self):
        return self._tick_task is not None and not self._tick_task.done()

    async def _tick_loop(self, tick_ms):
        interval = tick_ms / 1000.0
        try:
            while not self._closed:
                await asyncio.sleep(interval)
                async with self.lock:
                    changed = self.advance_time(tick_ms)
                    if changed:
                        await self.broadcast_snapshot()
        except asyncio.CancelledError:
            raise

    def advance_time(self, ms):
        """
        Advance engine time. Caller must hold self.lock.
        Returns True if visible game state changed.
        """
        self.engine.tick(ms)
        key = self._state_key()
        if key == self._last_state_key:
            return False
        self._last_state_key = key
        self.bump_sequence()
        return True

    def snapshot_payload(self):
        return snapshot_to_dict(
            self.engine.create_snapshot(),
            sequence=self.sequence,
        )

    async def broadcast_snapshot(self):
        payload = self.snapshot_payload()
        message = encode_message("state_snapshot", payload=payload)
        dead = []
        for websocket in list(self._connections):
            try:
                await websocket.send(message)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            self._connections.discard(websocket)

    def _state_key(self):
        snapshot = self.engine.create_snapshot()
        pieces = []
        for piece in snapshot.pieces:
            target = None
            if piece.target is not None:
                target = (piece.target.row, piece.target.col)
            state = piece.state.value if hasattr(piece.state, "value") else piece.state
            pieces.append((
                piece.color,
                piece.piece_type,
                piece.position.row,
                piece.position.col,
                state,
                piece.progress,
                target,
                piece.rest_progress,
            ))
        return (snapshot.game_over, tuple(pieces))
