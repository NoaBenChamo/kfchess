import asyncio

from websockets.asyncio.client import connect

from shared.protocol import decode_message, encode_message


class NetworkClient:
    """
    Thin WebSocket client for Stage B.1.

    Sends/receives protocol JSON envelopes. No game logic.
    """

    def __init__(self, uri):
        self._uri = uri
        self._websocket = None

    async def connect(self):
        self._websocket = await connect(self._uri)

    async def close(self):
        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None

    async def send_message(self, message_type, payload=None, request_id=None):
        if self._websocket is None:
            raise RuntimeError("not connected")
        raw = encode_message(message_type, payload=payload, request_id=request_id)
        await self._websocket.send(raw)

    async def receive_message(self):
        if self._websocket is None:
            raise RuntimeError("not connected")
        raw = await self._websocket.recv()
        return decode_message(raw)

    async def ping(self):
        await self.send_message("ping", payload={})
        return await self.receive_until("pong")

    async def send_move(self, command):
        """Send a course-style move command string (e.g. WQe2e5)."""
        await self.send_message("move", payload={"command": command})
        return await self.receive_until("move_accepted", also_accept_errors=True)

    async def receive_until(
        self,
        message_type,
        timeout=2.0,
        also_accept_errors=False,
    ):
        """
        Read messages until one of the expected type arrives.
        Skips unrelated traffic such as state_snapshot broadcasts.
        """
        deadline = asyncio.get_running_loop().time() + timeout
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise TimeoutError(f"timed out waiting for {message_type}")
            message = await asyncio.wait_for(
                self.receive_message(),
                timeout=remaining,
            )
            if message["type"] == message_type:
                return message
            if also_accept_errors and message["type"] == "error":
                return message

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
