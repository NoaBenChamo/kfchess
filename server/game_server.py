import asyncio
import logging
import uuid

from server.auth_service import AuthError, AuthService
from server.client_session import ClientSession
from server.clock import SystemClock
from server.config import (
    DISCONNECT_GRACE_MS,
    MATCHMAKING_ELO_RANGE,
    MATCHMAKING_TIMEOUT_MS,
    TICK_MS,
)
from server.dal.database import Database
from server.dal.repositories import GameRepository, UserRepository
from server.game_command_handler import GameCommandHandler
from server.game_registry import GameRegistry
from server.match import Match
from server.matchmaker import Matchmaker
from server.rating_service import RatingService
from server.room_manager import RoomManager, STATUS_WAITING
from server.snapshot_serializer import snapshot_to_dict
from shared.protocol import (
    INVALID_MESSAGE,
    INVALID_USERNAME,
    NOT_AUTHENTICATED,
    NOT_IN_GAME,
    ProtocolError,
    SPECTATOR_READ_ONLY,
    decode_message,
    encode_auth_ok,
    encode_error,
    encode_identity_assigned,
    encode_match_found,
    encode_matchmaking_timeout,
    encode_message,
    encode_player_disconnected,
    encode_player_reconnected,
    encode_room_update,
)

logger = logging.getLogger(__name__)

DEFAULT_GAME_ID = "default"


class GameServer:
    """
    WebSocket server for Stage E/F.

    Auth → play_request (matchmaking) or create_room/join_room → Match.
    Legacy identify still seats on the default match for older tests.
    """

    def __init__(
        self,
        registry=None,
        command_handler=None,
        tick_ms=TICK_MS,
        database=None,
        auth_service=None,
        matchmaker=None,
        room_manager=None,
        disconnect_grace_ms=DISCONNECT_GRACE_MS,
        clock=None,
    ):
        self._connections = set()
        self._sessions = {}
        self._registry = registry if registry is not None else GameRegistry()
        self._clock = clock if clock is not None else SystemClock()
        if DEFAULT_GAME_ID not in self._registry:
            self._registry.create_default()
        self._commands = (
            command_handler
            if command_handler is not None
            else GameCommandHandler()
        )
        self._tick_ms = tick_ms
        self._disconnect_grace_ms = disconnect_grace_ms
        self._started = False
        self._timeout_task = None
        self._rooms = room_manager if room_manager is not None else RoomManager()

        self._owns_database = database is None
        if database is None:
            self._database = Database(":memory:")
            self._database.connect()
            self._database.initialize_schema()
        else:
            self._database = database
            try:
                self._database.connection
            except RuntimeError:
                self._database.connect()
                self._database.initialize_schema()

        self._auth = (
            auth_service
            if auth_service is not None
            else AuthService(UserRepository(self._database))
        )
        users = UserRepository(self._database)
        games = GameRepository(self._database)
        self._users = users
        self._rating = RatingService(users, games)
        self._matchmaker = (
            matchmaker
            if matchmaker is not None
            else Matchmaker(
                elo_range=MATCHMAKING_ELO_RANGE,
                timeout_ms=MATCHMAKING_TIMEOUT_MS,
                clock=self._clock,
            )
        )

    @property
    def registry(self):
        return self._registry

    @property
    def database(self):
        return self._database

    @property
    def matchmaker(self):
        return self._matchmaker

    @property
    def rooms(self):
        return self._rooms

    async def start(self):
        if self._started:
            return
        for match in self._registry.all_matches():
            self._configure_match(match)
            await match.start_tick_loop(self._tick_ms)
        self._timeout_task = asyncio.create_task(
            self._matchmaking_timeout_loop(),
            name="matchmaking-timeout",
        )
        self._started = True
        logger.info(
            "game server started tick_ms=%s grace_ms=%s",
            self._tick_ms,
            self._disconnect_grace_ms,
        )

    def _configure_match(self, match):
        match.set_clock(self._clock)
        match.set_grace_ms(self._disconnect_grace_ms)
        match.set_game_over_handler(self._on_match_game_over)
        match.set_grace_expire_handler(self._on_grace_expired)

    def _new_match(self, game_id):
        match = Match(game_id, clock=self._clock)
        self._configure_match(match)
        return match

    async def stop(self):
        if self._timeout_task is not None:
            self._timeout_task.cancel()
            try:
                await self._timeout_task
            except asyncio.CancelledError:
                pass
            self._timeout_task = None
        for match in self._registry.all_matches():
            await match.stop()
        self._started = False
        if self._owns_database:
            self._database.close()
        logger.info("game server stopped")

    async def handler(self, websocket):
        self._connections.add(websocket)
        session = ClientSession(websocket)
        self._sessions[websocket] = session
        logger.info(
            "connection opened connection_id=%s live=%s",
            session.connection_id,
            len(self._connections),
        )
        try:
            async for raw in websocket:
                await self._handle_raw_message(websocket, raw)
        except Exception:
            logger.exception(
                "unexpected handler error connection_id=%s user_id=%s",
                session.connection_id,
                session.user_id,
            )
            raise
        finally:
            await self._on_connection_lost(session, websocket)
            self._connections.discard(websocket)
            self._sessions.pop(websocket, None)
            logger.info(
                "connection closed connection_id=%s user_id=%s live=%s",
                session.connection_id,
                session.user_id,
                len(self._connections),
            )

    async def _on_connection_lost(self, session, websocket):
        self._matchmaker.cancel(session.connection_id)

        match = None
        if session.game_id is not None:
            match = self._registry.get(session.game_id)
        if match is None:
            match = self._registry.get(DEFAULT_GAME_ID)

        if match is None:
            return

        # Incomplete private room / solo seat: discard immediately (no grace).
        if session.is_identified and session.role == "player":
            room = (
                self._rooms.get(match.room_id) if match.room_id is not None else None
            )
            incomplete = match.player_count() < 2 or (
                room is not None and room.status == STATUS_WAITING
            )
            if incomplete:
                await self._discard_incomplete_match(match, websocket, session)
                return

            color = match.detach_player(websocket)
            if color is None:
                return
            logger.info(
                "player disconnected game_id=%s color=%s user_id=%s grace_ms=%s",
                match.game_id,
                color,
                session.user_id,
                self._disconnect_grace_ms,
            )
            await match.broadcast_message(
                "player_disconnected",
                payload={
                    "color": color,
                    "grace_period_ms": self._disconnect_grace_ms,
                },
            )
            match.begin_disconnect_grace(
                color,
                on_expire=self._on_grace_expired,
                grace_ms=self._disconnect_grace_ms,
            )
            return

        was_spectator = session.role == "spectator"
        room_id = match.room_id
        match.release(websocket)
        if was_spectator and room_id is not None and session.user_id is not None:
            self._rooms.remove_user(room_id, session.user_id)
            logger.info(
                "spectator left room_id=%s game_id=%s user_id=%s",
                room_id,
                match.game_id,
                session.user_id,
            )
            await self._broadcast_room_update(match)

    async def _discard_incomplete_match(self, match, websocket, session):
        """Close a waiting/solo room so the code cannot be joined after creator leave."""
        room_id = match.room_id
        game_id = match.game_id
        match.release(websocket)
        if room_id is not None:
            self._rooms.discard(room_id)
            logger.info(
                "waiting room discarded room_id=%s game_id=%s user_id=%s",
                room_id,
                game_id,
                session.user_id,
            )
        if game_id != DEFAULT_GAME_ID:
            await match.stop()
            self._registry.unregister(game_id)

    async def _on_grace_expired(self, match, color):
        async with match.lock:
            seated = match.player_for_color(color)
            if seated is None or not seated.disconnected:
                return
            if match.engine.is_game_over():
                return
            match.engine.resign(color)
            match.disconnect_forfeit = True

        await match.broadcast_snapshot()
        await self._on_match_game_over(match)

    async def _matchmaking_timeout_loop(self):
        try:
            while True:
                await asyncio.sleep(0.5)
                await self._expire_matchmaking()
        except asyncio.CancelledError:
            raise

    async def _expire_matchmaking(self):
        for waiting in self._matchmaker.pop_expired():
            try:
                await waiting.session.websocket.send(encode_matchmaking_timeout())
            except Exception:
                logger.debug(
                    "failed to notify matchmaking timeout for %s",
                    waiting.connection_id,
                )

    async def _handle_raw_message(self, websocket, raw):
        try:
            message = decode_message(raw)
        except ProtocolError as exc:
            text = str(exc).lower()
            if "username" in text:
                code = INVALID_USERNAME
            else:
                code = INVALID_MESSAGE
            await websocket.send(encode_error(code, str(exc)))
            return

        message_type = message["type"]
        if message_type == "ping":
            response = encode_message("pong", payload={})
            if "request_id" in message:
                response = encode_message(
                    "pong",
                    payload={},
                    request_id=message["request_id"],
                )
            await websocket.send(response)
            return

        if message_type == "register":
            await self._handle_register(websocket, message)
            return

        if message_type == "login":
            await self._handle_login(websocket, message)
            return

        if message_type == "play_request":
            await self._handle_play_request(websocket, message)
            return

        if message_type == "cancel_matchmaking":
            await self._handle_cancel_matchmaking(websocket, message)
            return

        if message_type == "identify":
            await self._handle_identify(websocket, message)
            return

        if message_type == "create_room":
            await self._handle_create_room(websocket, message)
            return

        if message_type == "join_room":
            await self._handle_join_room(websocket, message)
            return

        if message_type == "move":
            await self._handle_move(websocket, message)
            return

        if message_type == "jump_request":
            await self._handle_jump(websocket, message)
            return

        if message_type == "leave_game":
            await self._handle_leave_game(websocket, message)
            return

        logger.info(
            "invalid request connection_id=%s type=%s",
            getattr(self._sessions.get(websocket), "connection_id", "?"),
            message_type,
        )
        await websocket.send(
            encode_error(
                INVALID_MESSAGE,
                f"unsupported type: {message_type}",
            )
        )

    async def _handle_register(self, websocket, message):
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return
        if session.is_authenticated:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "already authenticated")
            )
            return

        payload = message["payload"]
        try:
            user = self._auth.register(payload["username"], payload["password"])
        except AuthError as exc:
            await websocket.send(encode_error(exc.code, exc.message))
            return

        session.bind_user(user.id, user.username, user.rating)
        logger.info(
            "register ok connection_id=%s user_id=%s username=%s",
            session.connection_id,
            user.id,
            user.username,
        )
        await websocket.send(
            encode_auth_ok(user.id, user.username, user.rating)
        )
        await self._try_restore_disconnected_game(session)

    async def _handle_login(self, websocket, message):
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return
        if session.is_authenticated:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "already authenticated")
            )
            return

        payload = message["payload"]
        try:
            user = self._auth.login(payload["username"], payload["password"])
        except AuthError as exc:
            logger.info(
                "login failed connection_id=%s code=%s",
                session.connection_id,
                exc.code,
            )
            await websocket.send(encode_error(exc.code, exc.message))
            return

        session.bind_user(user.id, user.username, user.rating)
        logger.info(
            "login ok connection_id=%s user_id=%s username=%s",
            session.connection_id,
            user.id,
            user.username,
        )
        await websocket.send(
            encode_auth_ok(user.id, user.username, user.rating)
        )
        await self._try_restore_disconnected_game(session)

    async def _try_restore_disconnected_game(self, session):
        """If this user has a disconnected seat, restore it and send snapshot."""
        for match in self._registry.all_matches():
            color = match.reconnect_user(session, session.user_id)
            if color is None:
                continue

            opponent = "b" if color == "w" else "w"
            opp_session = match.player_for_color(opponent)
            await match.broadcast_message(
                "player_reconnected",
                payload={"color": color},
            )
            await session.websocket.send(
                encode_match_found(
                    game_id=match.game_id,
                    color=color,
                    opponent_username=(
                        opp_session.username if opp_session else ""
                    ),
                    opponent_rating=(
                        opp_session.rating if opp_session else 1200
                    ),
                )
            )
            await session.websocket.send(
                encode_message(
                    "state_snapshot",
                    payload=match.snapshot_payload(),
                )
            )
            return True
        return False

    async def _handle_play_request(self, websocket, message):
        del message
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return
        if not session.is_authenticated:
            await websocket.send(
                encode_error(NOT_AUTHENTICATED, "login before play_request")
            )
            return
        if session.is_identified or session.role is not None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "already in a game")
            )
            return

        # Already restoring / holding a disconnected seat — refuse new queue.
        for match in self._registry.all_matches():
            seated = match.player_for_color("w")
            if seated and seated.user_id == session.user_id:
                await websocket.send(
                    encode_error(INVALID_MESSAGE, "already in a game")
                )
                return
            seated = match.player_for_color("b")
            if seated and seated.user_id == session.user_id:
                await websocket.send(
                    encode_error(INVALID_MESSAGE, "already in a game")
                )
                return

        pair = self._matchmaker.enqueue(session)
        if pair is None:
            logger.info(
                "matchmaking waiting connection_id=%s user_id=%s rating=%s",
                session.connection_id,
                session.user_id,
                session.rating,
            )
            await websocket.send(
                encode_message("request_ok", payload={"status": "waiting"})
            )
            return

        earlier, newer = pair
        logger.info(
            "matchmaking matched user_ids=%s,%s",
            earlier.session.user_id,
            newer.session.user_id,
        )
        await self._start_matched_game(earlier.session, newer.session)

    async def _handle_cancel_matchmaking(self, websocket, message):
        del message
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return
        removed = self._matchmaker.cancel(session.connection_id)
        await websocket.send(
            encode_message(
                "request_ok",
                payload={"status": "cancelled" if removed else "not_waiting"},
            )
        )

    async def _start_matched_game(self, white_session, black_session):
        game_id = f"g_{uuid.uuid4().hex[:12]}"
        match = self._new_match(game_id)
        self._registry.register(match)
        if self._started:
            await match.start_tick_loop(self._tick_ms)

        async with match.lock:
            white_result = match.try_assign_player(
                white_session, white_session.username
            )
            black_result = match.try_assign_player(
                black_session, black_session.username
            )

        if not white_result["ok"] or not black_result["ok"]:
            logger.error("failed to seat matched players into %s", game_id)
            return

        self._maybe_start_rated_game(match)

        logger.info(
            "game created game_id=%s white=%s black=%s",
            game_id,
            white_session.username,
            black_session.username,
        )

        await white_session.websocket.send(
            encode_match_found(
                game_id=game_id,
                color="w",
                opponent_username=black_session.username,
                opponent_rating=black_session.rating or 1200,
            )
        )
        await black_session.websocket.send(
            encode_match_found(
                game_id=game_id,
                color="b",
                opponent_username=white_session.username,
                opponent_rating=white_session.rating or 1200,
            )
        )

        snapshot = match.snapshot_payload()
        raw_snapshot = encode_message("state_snapshot", payload=snapshot)
        await white_session.websocket.send(raw_snapshot)
        await black_session.websocket.send(raw_snapshot)

    async def _handle_create_room(self, websocket, message):
        del message
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return
        if not session.is_authenticated:
            await websocket.send(
                encode_error(NOT_AUTHENTICATED, "login before create_room")
            )
            return
        if session.role is not None or session.game_id is not None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "already in a game")
            )
            return

        self._matchmaker.cancel(session.connection_id)

        game_id = f"g_{uuid.uuid4().hex[:12]}"
        match = self._new_match(game_id)
        self._registry.register(match)
        if self._started:
            await match.start_tick_loop(self._tick_ms)

        room = self._rooms.create(game_id, session.user_id)
        match.room_id = room.room_id

        async with match.lock:
            result = match.try_assign_color(session, session.username, "w")

        if not result["ok"]:
            self._rooms.discard(room.room_id)
            await websocket.send(
                encode_error(result["error_code"], result["error_message"])
            )
            return

        logger.info(
            "room created room_id=%s game_id=%s user_id=%s",
            room.room_id,
            game_id,
            session.user_id,
        )
        await self._send_room_joined(session, match, role="player", color="w")

    async def _handle_join_room(self, websocket, message):
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return
        if not session.is_authenticated:
            await websocket.send(
                encode_error(NOT_AUTHENTICATED, "login before join_room")
            )
            return
        if session.role is not None or session.game_id is not None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "already in a game")
            )
            return

        room_id = message["payload"]["room_id"]
        self._matchmaker.cancel(session.connection_id)

        join = self._rooms.join(room_id, session.user_id)
        if not join["ok"]:
            logger.info(
                "room join failed room_id=%s user_id=%s code=%s",
                room_id,
                session.user_id,
                join["error_code"],
            )
            await websocket.send(
                encode_error(join["error_code"], join["error_message"])
            )
            return

        room = self._rooms.get(room_id)
        match = self._registry.get(room.match_id) if room else None
        if match is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "room match missing")
            )
            return

        async with match.lock:
            if join["role"] == "player":
                result = match.try_assign_color(
                    session, session.username, join["color"]
                )
            else:
                result = match.add_spectator(session, session.username)

        if not result.get("ok", True) and "error_code" in result:
            self._rooms.remove_user(room_id, session.user_id)
            await websocket.send(
                encode_error(result["error_code"], result["error_message"])
            )
            return

        if join["role"] == "player" and join["color"] == "b":
            self._maybe_start_rated_game(match)

        logger.info(
            "room joined room_id=%s game_id=%s user_id=%s role=%s color=%s",
            room.room_id,
            match.game_id,
            session.user_id,
            join["role"],
            join["color"],
        )
        await self._send_room_joined(
            session,
            match,
            role=join["role"],
            color=join["color"],
        )
        await self._broadcast_room_update(match, exclude=session)

    async def _send_room_joined(self, session, match, role, color):
        membership = match.room_membership_payload()
        room = self._rooms.get(match.room_id)
        status = room.status if room is not None else "waiting"
        await session.websocket.send(
            encode_room_update(
                room_id=match.room_id,
                game_id=match.game_id,
                players=membership["players"],
                spectators=membership["spectators"],
                status=status,
                role=role,
                color=color,
            )
        )
        if role == "player" and color in ("w", "b"):
            opponent = "b" if color == "w" else "w"
            opp = match.player_for_color(opponent)
            await session.websocket.send(
                encode_identity_assigned(
                    username=session.username,
                    color=color,
                    game_id=match.game_id,
                )
            )
            # Also send match_found so remote clients that wait on it keep working.
            await session.websocket.send(
                encode_match_found(
                    game_id=match.game_id,
                    color=color,
                    opponent_username=opp.username if opp else "",
                    opponent_rating=(opp.rating if opp else 1200) or 1200,
                )
            )
        await session.websocket.send(
            encode_message(
                "state_snapshot",
                payload=match.snapshot_payload(),
            )
        )

    async def _broadcast_room_update(self, match, exclude=None):
        if match.room_id is None:
            return
        membership = match.room_membership_payload()
        room = self._rooms.get(match.room_id)
        status = room.status if room is not None else "waiting"
        message = encode_room_update(
            room_id=match.room_id,
            game_id=match.game_id,
            players=membership["players"],
            spectators=membership["spectators"],
            status=status,
        )
        dead = []
        for websocket in list(match._connections):
            if exclude is not None and websocket is exclude.websocket:
                continue
            try:
                await websocket.send(message)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            match._connections.discard(websocket)

    async def _handle_identify(self, websocket, message):
        """Legacy Stage C seating on the default match."""
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return

        if not session.is_authenticated:
            await websocket.send(
                encode_error(
                    NOT_AUTHENTICATED,
                    "login or register before identify",
                )
            )
            return

        if session.is_identified:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "already identified")
            )
            return

        username = message["payload"]["username"]
        if username != session.username:
            await websocket.send(
                encode_error(
                    INVALID_MESSAGE,
                    "identify username must match authenticated user",
                )
            )
            return

        match = self._registry.get(DEFAULT_GAME_ID)
        if match is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "no active game")
            )
            return

        async with match.lock:
            result = match.try_assign_player(session, session.username)

        if not result["ok"]:
            await websocket.send(
                encode_error(result["error_code"], result["error_message"])
            )
            return

        self._maybe_start_rated_game(match)

        await websocket.send(
            encode_identity_assigned(
                username=session.username,
                color=result["color"],
                game_id=match.game_id,
            )
        )
        await websocket.send(
            encode_message(
                "state_snapshot",
                payload=match.snapshot_payload(),
            )
        )

    def _maybe_start_rated_game(self, match):
        if match.db_game_id is not None:
            return
        if match.player_count() != 2:
            return
        white = match.player_for_color("w")
        black = match.player_for_color("b")
        if (
            white is None
            or black is None
            or white.user_id is None
            or black.user_id is None
        ):
            return
        game = self._rating.start_game(white.user_id, black.user_id)
        match.db_game_id = game.id
        match.rated = True

    async def _on_match_game_over(self, match):
        if match._result_recorded:
            return

        winner = match.detect_winner_color()
        if match.disconnect_forfeit:
            reason = "disconnect"
        elif winner is not None:
            reason = "king_captured"
        else:
            reason = "game_over"
        logger.info(
            "game ended game_id=%s room_id=%s winner=%s reason=%s",
            match.game_id,
            match.room_id,
            winner,
            reason,
        )

        if match.db_game_id is None:
            match._result_recorded = True
            await match.broadcast_message(
                "game_over",
                payload={
                    "winner": winner,
                    "reason": reason,
                    "rated": False,
                    "ratings": {},
                },
            )
            if match.room_id is not None:
                self._rooms.mark_finished(match.game_id)
            match.clear_seats()
            return

        result = self._rating.finalize_game(
            match.db_game_id,
            winner,
            rated=match.rated,
        )
        match._result_recorded = True

        for color, info in result.get("ratings", {}).items():
            session = match.player_for_color(color)
            if session is not None:
                session.rating = info["rating_after"]

        await match.broadcast_message(
            "game_over",
            payload={
                "winner": result["winner_color"],
                "reason": reason,
                "rated": result["rated"],
                "ratings": result["ratings"],
                "game_id": result["game_id"],
            },
        )
        if match.room_id is not None:
            self._rooms.mark_finished(match.game_id)
        match.clear_seats()

    async def _handle_move(self, websocket, message):
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(
                    NOT_AUTHENTICATED,
                    "join a game before sending moves",
                )
            )
            return

        if session.role == "spectator":
            await websocket.send(
                encode_error(
                    SPECTATOR_READ_ONLY,
                    "spectators cannot move pieces",
                )
            )
            return

        if not session.is_identified:
            await websocket.send(
                encode_error(
                    NOT_AUTHENTICATED,
                    "join a game before sending moves",
                )
            )
            return

        if session.disconnected:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "reconnect before sending moves")
            )
            return

        game_id = session.game_id or DEFAULT_GAME_ID
        match = self._registry.get(game_id)
        if match is None:
            await websocket.send(
                encode_error(NOT_IN_GAME, "no active game")
            )
            return

        seated = match.player_for_color(session.assigned_color)
        if seated is None or seated.disconnected or seated is not session:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "seat is disconnected")
            )
            return

        command = message["payload"]["command"]
        async with match.lock:
            result = self._commands.apply_move_command(
                match,
                command,
                assigned_color=session.assigned_color,
            )

        if not result["ok"]:
            await websocket.send(
                encode_error(
                    result["error_code"],
                    result["error_message"],
                )
            )
            return

        await websocket.send(
            encode_message(
                "move_accepted",
                payload={
                    "command": result["command"],
                    "snapshot": result["snapshot"],
                },
            )
        )
        await match.broadcast_snapshot()

    async def _handle_jump(self, websocket, message):
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(
                    NOT_AUTHENTICATED,
                    "join a game before sending jumps",
                )
            )
            return

        if session.role == "spectator":
            await websocket.send(
                encode_error(
                    SPECTATOR_READ_ONLY,
                    "spectators cannot jump pieces",
                )
            )
            return

        if not session.is_identified:
            await websocket.send(
                encode_error(
                    NOT_AUTHENTICATED,
                    "join a game before sending jumps",
                )
            )
            return

        if session.disconnected:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "reconnect before sending jumps")
            )
            return

        game_id = session.game_id or DEFAULT_GAME_ID
        match = self._registry.get(game_id)
        if match is None:
            await websocket.send(
                encode_error(NOT_IN_GAME, "no active game")
            )
            return

        seated = match.player_for_color(session.assigned_color)
        if seated is None or seated.disconnected or seated is not session:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "seat is disconnected")
            )
            return

        payload = message["payload"]
        async with match.lock:
            result = self._commands.apply_jump_command(
                match,
                payload["row"],
                payload["col"],
                assigned_color=session.assigned_color,
            )

        if not result["ok"]:
            await websocket.send(
                encode_error(
                    result["error_code"],
                    result["error_message"],
                )
            )
            return

        await websocket.send(
            encode_message(
                "jump_accepted",
                payload={
                    "row": result["row"],
                    "col": result["col"],
                    "snapshot": result["snapshot"],
                },
            )
        )
        await match.broadcast_snapshot()

    async def _handle_leave_game(self, websocket, message):
        """
        Voluntary leave from the client Exit Game button.

        Spectators leave without affecting the match.
        Players forfeit immediately (same outcome as disconnect grace expiry).
        """
        del message
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return

        match = None
        if session.game_id is not None:
            match = self._registry.get(session.game_id)
        if match is None:
            match = self._registry.get(DEFAULT_GAME_ID)
        if match is None:
            await websocket.send(
                encode_error(NOT_IN_GAME, "no active game")
            )
            return

        if session.role == "spectator":
            room_id = match.room_id
            match.release(websocket)
            if room_id is not None and session.user_id is not None:
                self._rooms.remove_user(room_id, session.user_id)
                await self._broadcast_room_update(match)
            await websocket.send(
                encode_message("leave_ok", payload={"role": "spectator"})
            )
            return

        if session.role != "player" or session.assigned_color is None:
            await websocket.send(
                encode_error(NOT_IN_GAME, "not seated in a game")
            )
            return

        room = self._rooms.get(match.room_id) if match.room_id else None
        incomplete = match.player_count() < 2 or (
            room is not None and room.status == STATUS_WAITING
        )
        if incomplete:
            await self._discard_incomplete_match(match, websocket, session)
            await websocket.send(
                encode_message("leave_ok", payload={"role": "player"})
            )
            return

        color = session.assigned_color
        async with match.lock:
            if match.engine.is_game_over():
                match.release(websocket)
                await websocket.send(
                    encode_message("leave_ok", payload={"role": "player"})
                )
                return
            match.engine.resign(color)
            match.disconnect_forfeit = True

        logger.info(
            "player left game_id=%s color=%s user_id=%s",
            match.game_id,
            color,
            session.user_id,
        )
        await match.broadcast_snapshot()
        await self._on_match_game_over(match)
        await websocket.send(
            encode_message(
                "leave_ok",
                payload={"role": "player", "forfeit": True},
            )
        )

    def current_snapshot(self, game_id=DEFAULT_GAME_ID):
        match = self._registry.get(game_id)
        if match is None:
            return None
        return snapshot_to_dict(
            match.engine.create_snapshot(),
            sequence=match.sequence,
        )

    @property
    def connection_count(self):
        return len(self._connections)
