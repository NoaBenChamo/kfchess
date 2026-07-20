import asyncio
import queue
import threading

from client.client_state import ClientState
from client.network_client import NetworkClient


class RemoteSession:
    """
    Bridges the sync OpenCV loop and the async WebSocket client.
    """

    def __init__(self, uri):
        self._uri = uri
        self.state = ClientState()
        self._outgoing = queue.Queue()
        self._incoming = queue.Queue()
        self._thread = None
        self._ready = threading.Event()
        self._stopped = threading.Event()

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

    def pump(self):
        """Apply all pending network messages into ClientState."""
        while True:
            try:
                message = self._incoming.get_nowait()
            except queue.Empty:
                break
            self.state.handle_message(message)

    def send_move(self, command):
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
                self.state.handle_message(message)
                self._ready.set()
