import logging

from server.config import TICK_MS
from server.game_command_handler import GameCommandHandler
from server.game_registry import GameRegistry
from server.snapshot_serializer import snapshot_to_dict
from shared.protocol import ProtocolError, decode_message, encode_error, encode_message

logger = logging.getLogger(__name__)

DEFAULT_GAME_ID = "default"


class GameServer:
    """
    WebSocket server for Stage B.4.

    Connections join the default Match; snapshots are broadcast per-Match only.
    """

    def __init__(self, registry=None, command_handler=None, tick_ms=TICK_MS):
        self._connections = set()
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
        if match is not None:
            match.add_connection(websocket)
            await websocket.send(
                encode_message(
                    "state_snapshot",
                    payload=match.snapshot_payload(),
                )
            )
        logger.info("client connected (%s live)", len(self._connections))
        try:
            async for raw in websocket:
                await self._handle_raw_message(websocket, raw)
        finally:
            self._connections.discard(websocket)
            if match is not None:
                match.remove_connection(websocket)
            logger.info("client disconnected (%s live)", len(self._connections))

    async def _handle_raw_message(self, websocket, raw):
        try:
            message = decode_message(raw)
        except ProtocolError as exc:
            await websocket.send(
                encode_error("INVALID_MESSAGE", str(exc))
            )
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

        if message_type == "move":
            await self._handle_move(websocket, message)
            return

        await websocket.send(
            encode_error(
                "INVALID_MESSAGE",
                f"unsupported type: {message_type}",
            )
        )

    async def _handle_move(self, websocket, message):
        command = message["payload"]["command"]
        match = self._registry.get(DEFAULT_GAME_ID)
        if match is None:
            await websocket.send(
                encode_error("INVALID_MESSAGE", "no active game")
            )
            return

        async with match.lock:
            result = self._commands.apply_move_command(match, command)

        if not result["ok"]:
            await websocket.send(
                encode_error(
                    result["error_code"],
                    result["error_message"],
                )
            )
            return

        # Ack the mover, then broadcast the same snapshot to every peer in this Match.
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
