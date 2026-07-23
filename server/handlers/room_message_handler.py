"""Private rooms and legacy identify seating."""

import logging
import uuid

from server.session_role_enum import SessionRole

from shared.protocol import (
    INVALID_MESSAGE,
    NOT_AUTHENTICATED,
    encode_error,
    encode_identity_assigned,
    encode_match_found,
    encode_message,
    encode_room_update,
)

logger = logging.getLogger(__name__)


class RoomMessageHandler:
    """Create/join private rooms and legacy default-match identify."""

    def __init__(
        self,
        sessions,
        registry,
        rooms,
        matchmaker,
        *,
        default_game_id,
        create_match_fn,
        start_tick_if_running_fn,
        start_rated_fn,
    ):
        self._sessions = sessions
        self._registry = registry
        self._rooms = rooms
        self._matchmaker = matchmaker
        self._default_game_id = default_game_id
        self._create_match = create_match_fn
        self._start_tick_if_running = start_tick_if_running_fn
        self._start_rated = start_rated_fn

    async def handle_create_room(self, websocket, message):
        del message
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return
        if not session.is_authenticated:
            await websocket.send(
                encode_error(NOT_AUTHENTICATED, "login before create_room")
            )
            return
        if session.role is not None or session.game_id is not None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "already in a game")
            )
            return

        self._matchmaker.cancel(session.connection_id)

        game_id = f"g_{uuid.uuid4().hex[:12]}"
        match = self._create_match(game_id)
        self._registry.register(match)
        await self._start_tick_if_running(match)

        room = self._rooms.create(game_id, session.user_id)
        match.room_id = room.room_id

        async with match.lock:
            result = match.try_assign_color(session, session.username, "w")

        if not result["ok"]:
            self._rooms.discard(room.room_id)
            await websocket.send(
                encode_error(result["error_code"], result["error_message"])
            )
            return

        logger.info(
            "room created room_id=%s game_id=%s user_id=%s",
            room.room_id,
            game_id,
            session.user_id,
        )
        await self.send_room_joined(session, match, role=SessionRole.PLAYER, color="w")

    async def handle_join_room(self, websocket, message):
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return
        if not session.is_authenticated:
            await websocket.send(
                encode_error(NOT_AUTHENTICATED, "login before join_room")
            )
            return
        if session.role is not None or session.game_id is not None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "already in a game")
            )
            return

        room_id = message["payload"]["room_id"]
        self._matchmaker.cancel(session.connection_id)

        join = self._rooms.join(room_id, session.user_id)
        if not join["ok"]:
            logger.info(
                "room join failed room_id=%s user_id=%s code=%s",
                room_id,
                session.user_id,
                join["error_code"],
            )
            await websocket.send(
                encode_error(join["error_code"], join["error_message"])
            )
            return

        room = self._rooms.get(room_id)
        match = self._registry.get(room.match_id) if room else None
        if match is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "room match missing")
            )
            return

        async with match.lock:
            if join["role"] == SessionRole.PLAYER:
                result = match.try_assign_color(
                    session, session.username, join["color"]
                )
            else:
                result = match.add_spectator(session, session.username)

        if not result.get("ok", True) and "error_code" in result:
            self._rooms.remove_user(room_id, session.user_id)
            await websocket.send(
                encode_error(result["error_code"], result["error_message"])
            )
            return

        if join["role"] == SessionRole.PLAYER and join["color"] == "b":
            self._start_rated(match)

        logger.info(
            "room joined room_id=%s game_id=%s user_id=%s role=%s color=%s",
            room.room_id,
            match.game_id,
            session.user_id,
            join["role"],
            join["color"],
        )
        await self.send_room_joined(
            session,
            match,
            role=join["role"],
            color=join["color"],
        )
        await self.broadcast_room_update(match, exclude=session)

    async def send_room_joined(self, session, match, role, color):
        membership = match.room_membership_payload()
        room = self._rooms.get(match.room_id)
        status = room.status if room is not None else "waiting"
        await session.websocket.send(
            encode_room_update(
                room_id=match.room_id,
                game_id=match.game_id,
                players=membership["players"],
                spectators=membership["spectators"],
                status=status,
                role=role,
                color=color,
            )
        )
        if role == SessionRole.PLAYER and color in ("w", "b"):
            opponent = "b" if color == "w" else "w"
            opp = match.player_for_color(opponent)
            await session.websocket.send(
                encode_identity_assigned(
                    username=session.username,
                    color=color,
                    game_id=match.game_id,
                )
            )
            await session.websocket.send(
                encode_match_found(
                    game_id=match.game_id,
                    color=color,
                    opponent_username=opp.username if opp else "",
                    opponent_rating=(opp.rating if opp else 1200) or 1200,
                )
            )
        await session.websocket.send(
            encode_message(
                "state_snapshot",
                payload=match.snapshot_payload(),
            )
        )

    async def broadcast_room_update(self, match, exclude=None):
        if match.room_id is None:
            return
        membership = match.room_membership_payload()
        room = self._rooms.get(match.room_id)
        status = room.status if room is not None else "waiting"
        message = encode_room_update(
            room_id=match.room_id,
            game_id=match.game_id,
            players=membership["players"],
            spectators=membership["spectators"],
            status=status,
        )
        await match.broadcast_raw(message, exclude=exclude)

    async def handle_identify(self, websocket, message):
        """Legacy Stage C seating on the default match."""
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return

        if not session.is_authenticated:
            await websocket.send(
                encode_error(
                    NOT_AUTHENTICATED,
                    "login or register before identify",
                )
            )
            return

        if session.is_in_game:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "already identified")
            )
            return

        username = message["payload"]["username"]
        if username != session.username:
            await websocket.send(
                encode_error(
                    INVALID_MESSAGE,
                    "identify username must match authenticated user",
                )
            )
            return

        match = self._registry.get(self._default_game_id)
        if match is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "no active game")
            )
            return

        async with match.lock:
            result = match.try_assign_player(session, session.username)

        if not result["ok"]:
            await websocket.send(
                encode_error(result["error_code"], result["error_message"])
            )
            return

        self._start_rated(match)

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
