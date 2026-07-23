import asyncio
import logging

from server.auth_service import AuthService
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
from server.handlers.auth_message_handler import AuthMessageHandler
from server.handlers.game_message_handler import GameMessageHandler
from server.handlers.matchmaking_handler import MatchmakingHandler
from server.handlers.room_message_handler import RoomMessageHandler
from server.matchmaker import Matchmaker
from server.message_router import MessageRouter
from server.rating_service import RatingService
from server.room_manager import RoomManager
from server.services.connection_lifecycle_service import ConnectionLifecycleService
from server.services.game_result_service import GameResultService
from server.services.match_factory import MatchFactory
from server.snapshot_serializer import snapshot_to_dict

logger = logging.getLogger(__name__)

DEFAULT_GAME_ID = "default"


class GameServer:
    """
    GameServer manages client connections and coordinates server components.
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
        self._started = False
        self._timeout_task = None

        self._tick_ms = tick_ms
        self._disconnect_grace_ms = disconnect_grace_ms

        self._registry = registry or GameRegistry()
        self._clock = clock or SystemClock()
        self._commands = command_handler or GameCommandHandler()
        self._rooms = room_manager or RoomManager()

        if DEFAULT_GAME_ID not in self._registry:
            self._registry.create_default()

        self._initialize_database(database)
        self._initialize_services(auth_service, matchmaker)
        self._initialize_handlers()
        self._initialize_router()

    def _initialize_database(self, database):
        self._owns_database = database is None
        self._database = database or Database(":memory:")

        try:
            self._database.connection
        except RuntimeError:
            self._database.connect()
            self._database.initialize_schema()

    def _initialize_services(self, auth_service, matchmaker):
        users = UserRepository(self._database)
        games = GameRepository(self._database)

        self._users = users
        self._auth = auth_service or AuthService(users)
        self._rating = RatingService(users, games)

        self._matchmaker = matchmaker or Matchmaker(
            elo_range=MATCHMAKING_ELO_RANGE,
            timeout_ms=MATCHMAKING_TIMEOUT_MS,
            clock=self._clock,
        )

        self._results = GameResultService(self._rating, self._rooms)
        self._match_factory = MatchFactory(
            self._clock,
            self._disconnect_grace_ms,
            on_game_over=self._results.finalize_game_over,
            on_grace_expired=self._results.on_grace_expired,
        )

    def _initialize_handlers(self):
        async def start_tick_if_running(match):
            if self._started:
                await match.start_tick_loop(self._tick_ms)

        self._rooms_handler = RoomMessageHandler(
            self._sessions,
            self._registry,
            self._rooms,
            self._matchmaker,
            default_game_id=DEFAULT_GAME_ID,
            create_match_fn=self._match_factory.create,
            start_tick_if_running_fn=start_tick_if_running,
            start_rated_fn=self._results.maybe_start_rated_game,
        )

        self._connections_lifecycle = ConnectionLifecycleService(
            self._registry,
            self._rooms,
            self._matchmaker,
            default_game_id=DEFAULT_GAME_ID,
            disconnect_grace_ms=self._disconnect_grace_ms,
            on_grace_expired_fn=self._results.on_grace_expired,
            broadcast_room_update_fn=self._rooms_handler.broadcast_room_update,
        )

        self._auth_handler = AuthMessageHandler(
            self._sessions,
            self._auth,
            restore_fn=self._connections_lifecycle.try_restore_disconnected_game,
        )

        self._matchmaking = MatchmakingHandler(
            self._sessions,
            self._registry,
            self._matchmaker,
            create_match_fn=self._match_factory.create,
            start_tick_if_running_fn=start_tick_if_running,
            start_rated_fn=self._results.maybe_start_rated_game,
        )

        self._game_messages = GameMessageHandler(
            self._sessions,
            self._registry,
            self._commands,
            default_game_id=DEFAULT_GAME_ID,
            rooms=self._rooms,
            broadcast_room_update_fn=self._rooms_handler.broadcast_room_update,
            discard_incomplete_fn=self._connections_lifecycle.discard_incomplete_match,
            finalize_game_over_fn=self._results.finalize_game_over,
        )

    def _initialize_router(self):
        self._router = MessageRouter(
            {
                "register": self._auth_handler.handle_register,
                "login": self._auth_handler.handle_login,
                "play_request": self._matchmaking.handle_play_request,
                "cancel_matchmaking": self._matchmaking.handle_cancel_matchmaking,
                "identify": self._rooms_handler.handle_identify,
                "create_room": self._rooms_handler.handle_create_room,
                "join_room": self._rooms_handler.handle_join_room,
                "move": self._game_messages.handle_move,
                "jump_request": self._game_messages.handle_jump,
                "leave_game": self._game_messages.handle_leave_game,
            }
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
            self._match_factory.configure(match)
            await match.start_tick_loop(self._tick_ms)
        self._timeout_task = asyncio.create_task(
            self._matchmaking.timeout_loop(asyncio.sleep),
            name="matchmaking-timeout",
        )
        self._started = True
        logger.info(
            "game server started tick_ms=%s grace_ms=%s",
            self._tick_ms,
            self._disconnect_grace_ms,
        )

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
                await self._router.handle_raw(websocket, raw)
        except Exception:
            logger.exception(
                "unexpected handler error connection_id=%s user_id=%s",
                session.connection_id,
                session.user_id,
            )
            raise
        finally:
            await self._connections_lifecycle.on_connection_lost(session, websocket)
            self._connections.discard(websocket)
            self._sessions.pop(websocket, None)
            logger.info(
                "connection closed connection_id=%s user_id=%s live=%s",
                session.connection_id,
                session.user_id,
                len(self._connections),
            )

    # --- Test / backward-compatible wrappers ---

    async def _expire_matchmaking(self):
        await self._matchmaking.expire_matchmaking()

    async def _handle_raw_message(self, websocket, raw):
        await self._router.handle_raw(websocket, raw)

    async def _on_match_game_over(self, match):
        await self._results.finalize_game_over(match)

    async def _on_grace_expired(self, match, color):
        await self._results.on_grace_expired(match, color)

    async def _try_restore_disconnected_game(self, session):
        return await self._connections_lifecycle.try_restore_disconnected_game(
            session
        )

    async def _on_connection_lost(self, session, websocket):
        await self._connections_lifecycle.on_connection_lost(session, websocket)

    async def _discard_incomplete_match(self, match, websocket, session):
        await self._connections_lifecycle.discard_incomplete_match(
            match, websocket, session
        )

    def _configure_match(self, match):
        self._match_factory.configure(match)

    def _new_match(self, game_id):
        return self._match_factory.create(game_id)

    def _maybe_start_rated_game(self, match):
        self._results.maybe_start_rated_game(match)

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
