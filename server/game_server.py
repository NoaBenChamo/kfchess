import logging

from server.client_session import ClientSession
from server.config import TICK_MS
from server.game_command_handler import GameCommandHandler
from server.game_registry import GameRegistry
from server.snapshot_serializer import snapshot_to_dict
from shared.protocol import (
    INVALID_MESSAGE,
    INVALID_USERNAME,
    NOT_AUTHENTICATED,
    ProtocolError,
    decode_message,
    encode_error,
    encode_identity_assigned,
    encode_message,
)

logger = logging.getLogger(__name__)

DEFAULT_GAME_ID = "default"


class GameServer:
    """
    WebSocket server for Stage C.

    Connections must identify before joining a match seat and receiving snapshots.
    """

    def __init__(self, registry=None, command_handler=None, tick_ms=TICK_MS):
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

    @property
    def registry(self):
        return self._registry

    async def start(self):
        if self._started:
            return
        for match in self._registry.all_matches():
            await match.start_tick_loop(self._tick_ms)
        self._started = True

    async def stop(self):
        for match in self._registry.all_matches():
            await match.stop()
        self._started = False

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
            code = (
                INVALID_USERNAME
                if "username" in str(exc).lower()
                else INVALID_MESSAGE
            )
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

    async def _handle_identify(self, websocket, message):
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return

        if session.is_identified:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "already identified")
            )
            return

        match = self._registry.get(DEFAULT_GAME_ID)
        if match is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "no active game")
            )
            return

        username = message["payload"]["username"]
        async with match.lock:
            result = match.try_assign_player(session, username)

        if not result["ok"]:
            await websocket.send(
                encode_error(result["error_code"], result["error_message"])
            )
            return

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
