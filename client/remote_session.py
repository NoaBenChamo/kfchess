import asyncio
import queue
import threading

from client.client_state import ClientState
from client.network_client import NetworkClient
from client.snapshot_codec import piece_at
from model.position import Position
from shared.squares import position_to_square
from snapshots.game_snapshot import GameSnapshot


class RemoteSession:
    """
    Bridges the sync OpenCV loop and the async WebSocket client.

    Implements PlaySession for the remote client.
    """

    def __init__(self, uri):
        self._uri = uri
        self._state = ClientState()
        self._outgoing = queue.Queue()
        self._incoming = queue.Queue()
        self._thread = None
        self._ready = threading.Event()
        self._stopped = threading.Event()

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
        if not self._ready.wait(timeout=5.0):
            raise TimeoutError("timed out waiting for server snapshot")

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
        if piece_at(self._state.snapshot_dict, position) is None:
            return
        self._state.select(position)

    def clear_selection(self) -> None:
        self._state.clear_selection()

    def request_move_to(self, target: Position) -> None:
        selected = self._state.selected
        if selected is None:
            return

        piece = piece_at(self._state.snapshot_dict, selected)
        if piece is None:
            self._state.clear_selection()
            return

        color, piece_type = piece
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
        async with NetworkClient(self._uri) as client:
            receiver = asyncio.create_task(self._receive_loop(client))
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

    async def _receive_loop(self, client):
        while not self._stopped.is_set():
            message = await client.receive_message()
            self._incoming.put(message)
            if (
                message.get("type") == "state_snapshot"
                and not self._ready.is_set()
            ):
                self._state.handle_message(message)
                self._ready.set()
