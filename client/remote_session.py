import asyncio
import logging
import queue
import threading

from client.client_state import ClientState
from client.network_client import NetworkClient
from client.room_dialog import MODE_CREATE_ROOM, MODE_JOIN_ROOM, MODE_MATCHMAKING
from client.snapshot_codec import piece_at
from model.position import Position
from shared.squares import position_to_square
from snapshots.game_snapshot import GameSnapshot


logger = logging.getLogger(__name__)


class IdentifyError(RuntimeError):
    """Raised when the server rejects identify during RemoteSession.start()."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class RemoteSession:
    """
    Bridges the sync OpenCV loop and the async WebSocket client.

    Implements PlaySession for the remote client.
    """

    def __init__(
        self,
        uri,
        username,
        password,
        auth_mode="login",
        play_mode=MODE_MATCHMAKING,
        room_id=None,
    ):
        if auth_mode not in ("login", "register"):
            raise ValueError("auth_mode must be 'login' or 'register'")
        if play_mode not in (MODE_MATCHMAKING, MODE_CREATE_ROOM, MODE_JOIN_ROOM):
            raise ValueError("invalid play_mode")
        if play_mode == MODE_JOIN_ROOM and not room_id:
            raise ValueError("room_id is required for join_room")
        self._uri = uri
        self._username = username
        self._password = password
        self._auth_mode = auth_mode
        self._play_mode = play_mode
        self._room_id = room_id
        self._state = ClientState()
        self._outgoing = queue.Queue()
        self._incoming = queue.Queue()
        self._thread = None
        self._ready = threading.Event()
        self._stopped = threading.Event()
        self._startup_error = None

    @property
    def state(self):
        """Backward-compatible access to ClientState for tests and diagnostics."""
        return self._state

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._thread_main,
            name="remote-session",
            daemon=True,
        )
        self._thread.start()
        # Matchmaking can wait up to ~60s; allow a little slack.
        timeout = 70.0 if self._play_mode == MODE_MATCHMAKING else 15.0
        if not self._ready.wait(timeout=timeout):
            self.stop()
            raise TimeoutError("timed out waiting for match and snapshot")
        if self._startup_error is not None:
            self.stop()
            code = self._startup_error.get("code", "ERROR")
            message = self._startup_error.get("message", "matchmaking failed")
            raise IdentifyError(code, message)

    def stop(self):
        self._stopped.set()
        self._outgoing.put(None)
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def pump(self, elapsed_ms: int) -> None:
        """Apply all pending network messages into ClientState."""
        del elapsed_ms
        while True:
            try:
                message = self._incoming.get_nowait()
            except queue.Empty:
                break
            self._state.handle_message(message)

    def create_snapshot(self) -> GameSnapshot:
        return self._state.create_snapshot()

    def get_selected(self) -> Position | None:
        return self._state.selected

    def select(self, position: Position) -> None:
        if self._state.role == "spectator":
            return
        piece = piece_at(self._state.snapshot_dict, position)
        if piece is None:
            return
        color, _piece_type = piece
        assigned = self._state.assigned_color
        if assigned is not None and color.lower() != assigned.lower():
            return
        self._state.select(position)

    def clear_selection(self) -> None:
        self._state.clear_selection()

    def request_move_to(self, target: Position) -> None:
        if self._state.role == "spectator":
            return
        selected = self._state.selected
        if selected is None:
            return

        piece = piece_at(self._state.snapshot_dict, selected)
        if piece is None:
            self._state.clear_selection()
            return

        color, piece_type = piece
        assigned = self._state.assigned_color
        if assigned is not None and color.lower() != assigned.lower():
            self._state.clear_selection()
            return

        command = (
            f"{color.upper()}{piece_type}"
            f"{position_to_square(selected)}"
            f"{position_to_square(target)}"
        )
        self._send_move(command)
        self._state.clear_selection()

    def request_jump_to(self, target: Position) -> None:
        del target
        # Jump over the network is not wired yet.

    @property
    def game_over(self) -> bool:
        return self._state.game_over

    def _send_move(self, command):
        self._outgoing.put(("move", command))

    def _thread_main(self):
        asyncio.run(self._async_main())

    async def _async_main(self):
        try:
            logger.info("connecting uri=%s", self._uri)
            async with NetworkClient(self._uri) as client:
                receiver = asyncio.create_task(self._receive_loop(client))
                await client.send_message(
                    self._auth_mode,
                    payload={
                        "username": self._username,
                        "password": self._password,
                    },
                )
                try:
                    while not self._stopped.is_set():
                        try:
                            item = self._outgoing.get_nowait()
                        except queue.Empty:
                            await asyncio.sleep(0.01)
                            continue
                        if item is None:
                            break
                        kind, command = item
                        if kind == "move":
                            logger.debug("send type=move")
                            await client.send_message(
                                "move",
                                payload={"command": command},
                            )
                finally:
                    receiver.cancel()
                    try:
                        await receiver
                    except asyncio.CancelledError:
                        pass
        except Exception as exc:
            logger.exception("remote session connection error")
            if not self._ready.is_set():
                self._startup_error = {
                    "code": "CONNECTION_ERROR",
                    "message": str(exc),
                }
                self._ready.set()
            raise

    async def _receive_loop(self, client):
        play_sent = False
        while not self._stopped.is_set():
            message = await client.receive_message()
            message_type = message.get("type")
            logger.debug("recv type=%s", message_type)
            self._incoming.put(message)
            if self._ready.is_set():
                continue

            self._state.handle_message(message)
            if message_type == "error":
                # Ignore play_request rejection if we were already restored into a game.
                if (
                    self._state.assigned_color is not None
                    and (message.get("payload") or {}).get("message")
                    == "already in a game"
                ):
                    continue
                self._startup_error = message.get("payload") or {
                    "code": "ERROR",
                    "message": "auth or matchmaking failed",
                }
                self._ready.set()
                continue

            if message_type == "matchmaking_timeout":
                self._startup_error = {
                    "code": "MATCHMAKING_TIMEOUT",
                    "message": "no opponent found in time",
                }
                self._ready.set()
                continue

            if message_type == "auth_ok" and not play_sent:
                play_sent = True

                async def _enter_play_unless_restored():
                    await asyncio.sleep(0.05)
                    if self._stopped.is_set() or self._state.ready:
                        return
                    if self._play_mode == MODE_CREATE_ROOM:
                        logger.info("create_room")
                        await client.send_message("create_room", payload={})
                    elif self._play_mode == MODE_JOIN_ROOM:
                        logger.info("join_room room_id=%s", self._room_id)
                        await client.send_message(
                            "join_room",
                            payload={"room_id": self._room_id},
                        )
                    else:
                        logger.info("play_request")
                        await client.send_message("play_request", payload={})

                asyncio.create_task(_enter_play_unless_restored())
                continue

            if self._state.ready:
                self._ready.set()
