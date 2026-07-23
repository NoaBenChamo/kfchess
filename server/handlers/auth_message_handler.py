"""Authentication message handlers: register and login."""

import logging

from server.auth_service import AuthError
from shared.protocol import INVALID_MESSAGE, encode_auth_ok, encode_error

logger = logging.getLogger(__name__)


class AuthMessageHandler:
    """Authenticate a connection and bind the user to its ClientSession."""

    def __init__(self, sessions, auth_service, restore_fn):
        self._sessions = sessions
        self._auth = auth_service
        self._restore_fn = restore_fn

    async def handle_register(self, websocket, message):
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

        session.set_user(user.id, user.username, user.rating)
        logger.info(
            "register ok connection_id=%s user_id=%s username=%s",
            session.connection_id,
            user.id,
            user.username,
        )
        await websocket.send(
            encode_auth_ok(user.id, user.username, user.rating)
        )
        await self._restore_fn(session)

    async def handle_login(self, websocket, message):
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
            logger.info(
                "login failed connection_id=%s code=%s",
                session.connection_id,
                exc.code,
            )
            await websocket.send(encode_error(exc.code, exc.message))
            return

        session.set_user(user.id, user.username, user.rating)
        logger.info(
            "login ok connection_id=%s user_id=%s username=%s",
            session.connection_id,
            user.id,
            user.username,
        )
        await websocket.send(
            encode_auth_ok(user.id, user.username, user.rating)
        )
        await self._restore_fn(session)
