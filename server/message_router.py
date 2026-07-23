"""Protocol message decode and dispatch — no business logic."""

import logging

from shared.protocol import (
    INVALID_MESSAGE,
    INVALID_USERNAME,
    ProtocolError,
    decode_message,
    encode_error,
    encode_message,
)

logger = logging.getLogger(__name__)


class MessageRouter:
    """
    MessageRouter handles messages from the client
    by forwarding each message to the relevant handler.
    """

    def __init__(self, handlers):
        self._handlers = dict(handlers)


    async def handle_raw(self, websocket, raw):
        try:
            message = decode_message(raw)
        except ProtocolError as exc:
            await self._send_protocol_error(websocket, exc)
            return

        if message["type"] == "ping":
            await self._send_pong(websocket, message)
            return

        await self._dispatch(websocket, message)


    async def _send_protocol_error(self, websocket, exc):
        text = str(exc).lower()
        code = INVALID_USERNAME if "username" in text else INVALID_MESSAGE
        await websocket.send(encode_error(code, str(exc)))


    async def _send_pong(self, websocket, message):
        request_id = message.get("request_id")

        if request_id is None:
            response = encode_message("pong", payload={})
        else:
            response = encode_message(
                "pong",
                payload={},
                request_id=request_id,
            )

        await websocket.send(response)


    async def _dispatch(self, websocket, message):
        message_type = message["type"]
        handler = self._handlers.get(message_type)

        if handler is None:
            logger.info("invalid request type=%s", message_type)
            await websocket.send(
                encode_error(
                    INVALID_MESSAGE,
                    f"unsupported type: {message_type}",
                )
            )
            return

        await handler(websocket, message)