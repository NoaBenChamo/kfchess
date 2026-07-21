import logging

from server.auth_service import AuthError, AuthService
from server.client_session import ClientSession
from server.config import TICK_MS
from server.dal.database import Database
from server.dal.repositories import GameRepository, UserRepository
from server.game_command_handler import GameCommandHandler
from server.game_registry import GameRegistry
from server.rating_service import RatingService
from server.snapshot_serializer import snapshot_to_dict
from shared.protocol import (
    INVALID_MESSAGE,
    INVALID_USERNAME,
    NOT_AUTHENTICATED,
    ProtocolError,
    decode_message,
    encode_auth_ok,
    encode_error,
    encode_game_over,
    encode_identity_assigned,
    encode_message,
)

logger = logging.getLogger(__name__)

DEFAULT_GAME_ID = "default"


class GameServer:
    """
    WebSocket server for Stage D.

    Connections must register/login, then identify into a match seat.
    """

    def __init__(
        self,
        registry=None,
        command_handler=None,
        tick_ms=TICK_MS,
        database=None,
        auth_service=None,
    ):
        self._connections = set()
        self._sessions = {}
        self._registry = registry if registry is not None else GameRegistry()
        if DEFAULT_GAME_ID not in self._registry:
            self._registry.create_default()
        self._commands = (
            command_handler
            if command_handler is not None
            else GameCommandHandler()
        )
        self._tick_ms = tick_ms
        self._started = False

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

    @property
    def registry(self):
        return self._registry

    @property
    def database(self):
        return self._database

    async def start(self):
        if self._started:
            return
        for match in self._registry.all_matches():
            match.set_game_over_handler(self._on_match_game_over)
            await match.start_tick_loop(self._tick_ms)
        self._started = True

    async def stop(self):
        for match in self._registry.all_matches():
            await match.stop()
        self._started = False
        if self._owns_database:
            self._database.close()

    async def handler(self, websocket):
        match = self._registry.get(DEFAULT_GAME_ID)
        self._connections.add(websocket)
        self._sessions[websocket] = ClientSession(websocket)
        logger.info("client connected (%s live)", len(self._connections))
        try:
            async for raw in websocket:
                await self._handle_raw_message(websocket, raw)
        finally:
            self._connections.discard(websocket)
            self._sessions.pop(websocket, None)
            if match is not None:
                match.release(websocket)
            logger.info("client disconnected (%s live)", len(self._connections))

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

        if message_type == "identify":
            await self._handle_identify(websocket, message)
            return

        if message_type == "move":
            await self._handle_move(websocket, message)
            return

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
        await websocket.send(
            encode_auth_ok(user.id, user.username, user.rating)
        )

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
            await websocket.send(encode_error(exc.code, exc.message))
            return

        session.bind_user(user.id, user.username, user.rating)
        await websocket.send(
            encode_auth_ok(user.id, user.username, user.rating)
        )

    async def _handle_identify(self, websocket, message):
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
        reason = "king_captured" if winner is not None else "game_over"

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

    async def _handle_move(self, websocket, message):
        session = self._sessions.get(websocket)
        if session is None or not session.is_identified:
            await websocket.send(
                encode_error(
                    NOT_AUTHENTICATED,
                    "identify before sending moves",
                )
            )
            return

        command = message["payload"]["command"]
        match = self._registry.get(DEFAULT_GAME_ID)
        if match is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "no active game")
            )
            return

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
