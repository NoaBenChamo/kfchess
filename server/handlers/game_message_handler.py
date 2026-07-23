"""Gameplay message handlers: move, jump, leave."""

import logging

from server.room_manager import STATUS_WAITING
from server.session_role_enum import SessionRole
from shared.protocol import (
    INVALID_MESSAGE,
    NOT_AUTHENTICATED,
    NOT_IN_GAME,
    SPECTATOR_READ_ONLY,
    encode_error,
    encode_message,
)

logger = logging.getLogger(__name__)


class GameMessageHandler:
    """Handle in-game player actions (move / jump / leave)."""

    def __init__(
        self,
        sessions,
        registry,
        command_handler,
        *,
        default_game_id,
        rooms,
        broadcast_room_update_fn,
        discard_incomplete_fn,
        finalize_game_over_fn,
    ):
        self._sessions = sessions
        self._registry = registry
        self._commands = command_handler
        self._default_game_id = default_game_id
        self._rooms = rooms
        self._broadcast_room_update = broadcast_room_update_fn
        self._discard_incomplete = discard_incomplete_fn
        self._finalize_game_over = finalize_game_over_fn

    async def _require_active_player(self, websocket, kind):
        """
        Shared gate for move/jump only (not leave).

        ``kind`` is ``\"move\"`` or ``\"jump\"``.
        Returns (session, match) or None after sending an error.
        """
        plural = "moves" if kind == "move" else "jumps"
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(
                    NOT_AUTHENTICATED,
                    f"join a game before sending {plural}",
                )
            )
            return None

        if session.role == SessionRole.SPECTATOR:
            await websocket.send(
                encode_error(
                    SPECTATOR_READ_ONLY,
                    f"spectators cannot {kind} pieces",
                )
            )
            return None

        if not session.is_in_game:
            await websocket.send(
                encode_error(
                    NOT_AUTHENTICATED,
                    f"join a game before sending {plural}",
                )
            )
            return None

        if session.disconnected:
            await websocket.send(
                encode_error(
                    INVALID_MESSAGE,
                    f"reconnect before sending {plural}",
                )
            )
            return None

        game_id = session.game_id or self._default_game_id
        match = self._registry.get(game_id)
        if match is None:
            await websocket.send(encode_error(NOT_IN_GAME, "no active game"))
            return None

        seated = match.player_for_color(session.assigned_color)
        if seated is None or seated.disconnected or seated is not session:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "seat is disconnected")
            )
            return None

        return session, match

    async def handle_move(self, websocket, message):
        resolved = await self._require_active_player(websocket, "move")
        if resolved is None:
            return
        session, match = resolved

        command = message["payload"]["command"]
        async with match.lock:
            result = self._commands.apply_move_command(
                match,
                command,
                assigned_color=session.assigned_color,
            )

        if not result["ok"]:
            await websocket.send(
                encode_error(result["error_code"], result["error_message"])
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

    async def handle_jump(self, websocket, message):
        resolved = await self._require_active_player(websocket, "jump")
        if resolved is None:
            return
        session, match = resolved

        payload = message["payload"]
        async with match.lock:
            result = self._commands.apply_jump_command(
                match,
                payload["row"],
                payload["col"],
                assigned_color=session.assigned_color,
            )

        if not result["ok"]:
            await websocket.send(
                encode_error(result["error_code"], result["error_message"])
            )
            return

        await websocket.send(
            encode_message(
                "jump_accepted",
                payload={
                    "row": result["row"],
                    "col": result["col"],
                    "snapshot": result["snapshot"],
                },
            )
        )
        await match.broadcast_snapshot()

    async def handle_leave_game(self, websocket, message):
        """
        Voluntary leave from the client Exit Game button.

        Spectators leave without affecting the match.
        Players forfeit immediately (same outcome as disconnect grace expiry).
        """
        del message
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return

        match = None
        if session.game_id is not None:
            match = self._registry.get(session.game_id)
        if match is None:
            match = self._registry.get(self._default_game_id)
        if match is None:
            await websocket.send(encode_error(NOT_IN_GAME, "no active game"))
            return

        if session.role == SessionRole.SPECTATOR:
            room_id = match.room_id
            match.release(websocket)
            if room_id is not None and session.user_id is not None:
                self._rooms.remove_user(room_id, session.user_id)
                await self._broadcast_room_update(match)
            await websocket.send(
                encode_message("leave_ok", payload={"role": SessionRole.SPECTATOR})
            )
            return

        if session.role != SessionRole.PLAYER or session.assigned_color is None:
            await websocket.send(
                encode_error(NOT_IN_GAME, "not seated in a game")
            )
            return

        room = self._rooms.get(match.room_id) if match.room_id else None
        incomplete = match.player_count() < 2 or (
            room is not None and room.status == STATUS_WAITING
        )
        if incomplete:
            await self._discard_incomplete(match, websocket, session)
            await websocket.send(
                encode_message("leave_ok", payload={"role": SessionRole.PLAYER})
            )
            return

        color = session.assigned_color
        async with match.lock:
            if match.engine.is_game_over():
                match.release(websocket)
                await websocket.send(
                    encode_message("leave_ok", payload={"role": SessionRole.PLAYER})
                )
                return
            match.engine.resign(color)
            match.disconnect_forfeit = True

        logger.info(
            "player left game_id=%s color=%s user_id=%s",
            match.game_id,
            color,
            session.user_id,
        )
        await match.broadcast_snapshot()
        await self._finalize_game_over(match)
        await websocket.send(
            encode_message(
                "leave_ok",
                payload={"role": SessionRole.PLAYER, "forfeit": True},
            )
        )
