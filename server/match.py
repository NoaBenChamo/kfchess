import asyncio
import logging

from board_io.board_parser import BoardParser
from engine.game_engine import GameEngine
from server.opening_board import STANDARD_OPENING
from server.snapshot_serializer import snapshot_to_dict
from shared.protocol import INVALID_MESSAGE, SERVER_FULL, USERNAME_TAKEN, encode_message

logger = logging.getLogger(__name__)

_PLAYER_COLORS = ("w", "b")


class Match:
    """
    One authoritative networked game: owns GameEngine, sequence, and tick loop.

    Stage C also owns player seats (White / Black) via ClientSession.
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
        self._players = {}  # color -> ClientSession
        self._spectators = {}  # connection_id -> ClientSession
        self._sessions_by_ws = {}  # websocket -> ClientSession
        self._closed = False
        self._tick_task = None
        self._last_state_key = self._state_key()
        self.db_game_id = None
        self.rated = False
        self._result_recorded = False
        self._game_over_handler = None
        self._grace_tasks = {}
        self._grace_ms = 20_000
        self.room_id = None

    def set_grace_ms(self, grace_ms):
        self._grace_ms = grace_ms

    def set_game_over_handler(self, handler):
        """Optional async callback: await handler(match) once when game ends."""
        self._game_over_handler = handler

    def player_for_color(self, color):
        return self._players.get(color)

    def detect_winner_color(self):
        """Prefer arbiter winner (king capture); fall back to remaining kings."""
        winner = self.engine.get_winner()
        if winner is not None:
            return winner

        white_king = False
        black_king = False
        for piece in self.engine.create_snapshot().pieces:
            if piece.piece_type != "K":
                continue
            if piece.color.lower() == "w":
                white_king = True
            else:
                black_king = True
        if white_king and not black_king:
            return "w"
        if black_king and not white_king:
            return "b"
        return None

    def bump_sequence(self):
        self.sequence += 1
        return self.sequence

    def add_connection(self, websocket):
        self._connections.add(websocket)

    def remove_connection(self, websocket):
        self._connections.discard(websocket)

    def session_for(self, websocket):
        return self._sessions_by_ws.get(websocket)

    def player_count(self):
        return len(self._players)

    def spectator_count(self):
        return len(self._spectators)

    def spectators(self):
        return list(self._spectators.values())

    def is_full(self):
        return len(self._players) >= len(_PLAYER_COLORS)

    def is_username_taken(self, username):
        target = username.casefold()
        return any(
            session.username is not None
            and session.username.casefold() == target
            for session in self._players.values()
        )

    def try_assign_player(self, session, username):
        """
        Seat an identified player as White then Black.

        Returns:
            {"ok": True, "color": "w"|"b"} on success, or
            {"ok": False, "error_code": SERVER_FULL|USERNAME_TAKEN, "error_message": ...}
        """
        if self.is_username_taken(username):
            return {
                "ok": False,
                "error_code": USERNAME_TAKEN,
                "error_message": "username already seated in this match",
            }

        if self.is_full():
            return {
                "ok": False,
                "error_code": SERVER_FULL,
                "error_message": "match already has two players",
            }

        color = next(c for c in _PLAYER_COLORS if c not in self._players)
        session.bind_player(username, color, self.game_id)
        self._players[color] = session
        self._sessions_by_ws[session.websocket] = session
        self.add_connection(session.websocket)
        return {"ok": True, "color": color}

    def try_assign_color(self, session, username, color):
        """Seat a player into an explicit color (used by private rooms)."""
        if color not in _PLAYER_COLORS:
            return {
                "ok": False,
                "error_code": INVALID_MESSAGE,
                "error_message": "invalid color",
            }
        if color in self._players:
            return {
                "ok": False,
                "error_code": SERVER_FULL,
                "error_message": f"color {color} already seated",
            }
        if self.is_username_taken(username):
            return {
                "ok": False,
                "error_code": USERNAME_TAKEN,
                "error_message": "username already seated in this match",
            }
        session.bind_player(username, color, self.game_id)
        self._players[color] = session
        self._sessions_by_ws[session.websocket] = session
        self.add_connection(session.websocket)
        return {"ok": True, "color": color}

    def add_spectator(self, session, username):
        session.bind_spectator(username, self.game_id)
        self._spectators[session.connection_id] = session
        self._sessions_by_ws[session.websocket] = session
        self.add_connection(session.websocket)
        return {"ok": True, "role": "spectator"}

    def room_membership_payload(self):
        players = {}
        for color in _PLAYER_COLORS:
            seated = self._players.get(color)
            if seated is not None and seated.username:
                players[color] = {"username": seated.username}
        spectators = [
            {"username": session.username}
            for session in self._spectators.values()
            if session.username
        ]
        return {
            "players": players,
            "spectators": spectators,
        }

    def release(self, websocket):
        """
        Remove a connection and free its player seat / spectator slot if any.
        Safe to call when the websocket was never seated.
        """
        session = self._sessions_by_ws.pop(websocket, None)
        if session is not None:
            if session.assigned_color in self._players:
                if self._players.get(session.assigned_color) is session:
                    del self._players[session.assigned_color]
            self._spectators.pop(session.connection_id, None)
            session.clear_identity()
        self.remove_connection(websocket)
        return session

    def detach_player(self, websocket):
        """
        Drop a websocket but keep the player seat during disconnect grace.

        Returns:
            assigned color when a player seat is held for grace, else None.
            Spectators / unknown sockets are removed with no grace.
        """
        session = self._sessions_by_ws.pop(websocket, None)
        self.remove_connection(websocket)
        if session is None:
            return None

        if session.role == "spectator":
            self._spectators.pop(session.connection_id, None)
            session.clear_seat()
            return None

        if session.role != "player" or session.assigned_color is None:
            return None

        if self.engine.is_game_over():
            color = session.assigned_color
            if self._players.get(color) is session:
                del self._players[color]
            session.clear_seat()
            return None

        session.disconnected = True
        session.websocket = None
        return session.assigned_color

    def cancel_grace(self, color):
        task = self._grace_tasks.pop(color, None)
        if task is not None and not task.done():
            task.cancel()

    async def begin_disconnect_grace(self, color, on_expire, grace_ms=None):
        """Start (or restart) one grace timer per disconnected color."""
        self.cancel_grace(color)
        delay_ms = self._grace_ms if grace_ms is None else grace_ms

        async def _runner():
            try:
                await asyncio.sleep(delay_ms / 1000.0)
            except asyncio.CancelledError:
                return
            await on_expire(self, color)

        self._grace_tasks[color] = asyncio.create_task(
            _runner(),
            name=f"grace-{self.game_id}-{color}",
        )

    def reconnect_user(self, new_session, user_id):
        """
        Reattach a logged-in user to a disconnected seat.

        Returns color on success, or None if no seat / game already over.
        """
        if self.engine.is_game_over():
            return None

        for color, seated in self._players.items():
            if seated.user_id != user_id or not seated.disconnected:
                continue
            self.cancel_grace(color)
            new_session.bind_user(seated.user_id, seated.username, seated.rating)
            new_session.bind_player(seated.username, color, self.game_id)
            new_session.disconnected = False
            self._players[color] = new_session
            self._sessions_by_ws[new_session.websocket] = new_session
            self.add_connection(new_session.websocket)
            return color
        return None

    def clear_seats(self):
        for color in list(self._grace_tasks):
            self.cancel_grace(color)
        for session in list(self._players.values()):
            session.clear_seat()
        for session in list(self._spectators.values()):
            session.clear_seat()
        self._players.clear()
        self._spectators.clear()
        self._sessions_by_ws.clear()
        self._connections.clear()

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
        for color in list(self._grace_tasks):
            self.cancel_grace(color)
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
                just_ended = False
                async with self.lock:
                    was_over = self.engine.is_game_over()
                    changed = self.advance_time(tick_ms)
                    just_ended = self.engine.is_game_over() and not was_over
                    if changed:
                        await self.broadcast_snapshot()
                if just_ended and self._game_over_handler is not None:
                    await self._game_over_handler(self)
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
        await self._broadcast_raw(message)

    async def broadcast_message(self, message_type, payload):
        message = encode_message(message_type, payload=payload)
        await self._broadcast_raw(message)

    async def _broadcast_raw(self, message):
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
