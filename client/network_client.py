import asyncio

from websockets.asyncio.client import connect

from shared.protocol import decode_message, encode_message


class NetworkClient:
    """
    WebSocket client for sending/receiving protocol JSON envelopes

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

    async def register(self, username, password):
        await self.send_message(
            "register",
            payload={"username": username, "password": password},
        )
        return await self.receive_until("auth_ok", also_accept_errors=True)

    async def login(self, username, password):
        await self.send_message(
            "login",
            payload={"username": username, "password": password},
        )
        return await self.receive_until("auth_ok", also_accept_errors=True)

    async def identify(self, username):
        """Send identify and wait for identity_assigned or error."""
        await self.send_message("identify", payload={"username": username})
        return await self.receive_until(
            "identity_assigned",
            also_accept_errors=True,
        )

    async def play_request(self):
        """Join the matchmaking queue; returns request_ok, match_found, or error."""
        await self.send_message("play_request", payload={})
        return await self.receive_until(
            "match_found",
            also_accept_errors=True,
            also_accept=("request_ok", "matchmaking_timeout"),
        )

    async def cancel_matchmaking(self):
        await self.send_message("cancel_matchmaking", payload={})
        return await self.receive_until("request_ok", also_accept_errors=True)

    async def create_room(self):
        await self.send_message("create_room", payload={})
        return await self.receive_until(
            "room_update",
            also_accept_errors=True,
        )

    async def join_room(self, room_id):
        await self.send_message("join_room", payload={"room_id": room_id})
        return await self.receive_until(
            "room_update",
            also_accept_errors=True,
        )

    async def send_move(self, command):
        """Send a course-style move command string (e.g. WQe2e5)."""
        await self.send_message("move", payload={"command": command})
        return await self.receive_until("move_accepted", also_accept_errors=True)

    async def send_jump(self, row, col):
        """Send a jump-in-place request for the piece at (row, col)."""
        await self.send_message("jump_request", payload={"row": row, "col": col})
        return await self.receive_until("jump_accepted", also_accept_errors=True)

    async def leave_game(self):
        """Voluntary leave / forfeit; returns leave_ok, game_over, or error."""
        await self.send_message("leave_game", payload={})
        return await self.receive_until(
            "leave_ok",
            also_accept_errors=True,
            also_accept=("game_over",),
        )

    async def receive_until(
        self,
        message_type,
        timeout=2.0,
        also_accept_errors=False,
        also_accept=(),
    ):
        """
        Read messages until one of the expected type arrives.
        Skips unrelated traffic such as state_snapshot broadcasts.
        """
        accepted = {message_type, *also_accept}
        deadline = asyncio.get_running_loop().time() + timeout
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise TimeoutError(f"timed out waiting for {message_type}")
            message = await asyncio.wait_for(
                self.receive_message(),
                timeout=remaining,
            )
            if message["type"] in accepted:
                return message
            if also_accept_errors and message["type"] == "error":
                return message

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
