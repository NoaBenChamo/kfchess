"""Disconnect, waiting-room discard, and reconnect restore."""

import logging

from server.room_manager import STATUS_WAITING
from server.session_role_enum import SessionRole
from shared.protocol import encode_match_found, encode_message

logger = logging.getLogger(__name__)


class ConnectionLifecycleService:
    """Handle connection loss, incomplete-room cleanup, and seat restore."""

    def __init__(
        self,
        registry,
        rooms,
        matchmaker,
        *,
        default_game_id,
        disconnect_grace_ms,
        on_grace_expired_fn,
        broadcast_room_update_fn,
    ):
        self._registry = registry
        self._rooms = rooms
        self._matchmaker = matchmaker
        self._default_game_id = default_game_id
        self._disconnect_grace_ms = disconnect_grace_ms
        self._on_grace_expired = on_grace_expired_fn
        self._broadcast_room_update = broadcast_room_update_fn

    async def on_connection_lost(self, session, websocket):
        self._matchmaker.cancel(session.connection_id)

        match = None
        if session.game_id is not None:
            match = self._registry.get(session.game_id)
        if match is None:
            match = self._registry.get(self._default_game_id)

        if match is None:
            return

        if session.is_in_game and session.role == SessionRole.PLAYER:
            room = (
                self._rooms.get(match.room_id) if match.room_id is not None else None
            )
            incomplete = match.player_count() < 2 or (
                room is not None and room.status == STATUS_WAITING
            )
            if incomplete:
                await self.discard_incomplete_match(match, websocket, session)
                return

            color = match.detach_player(websocket)
            if color is None:
                return
            logger.info(
                "player disconnected game_id=%s color=%s user_id=%s grace_ms=%s",
                match.game_id,
                color,
                session.user_id,
                self._disconnect_grace_ms,
            )
            await match.broadcast_message(
                "player_disconnected",
                payload={
                    "color": color,
                    "grace_period_ms": self._disconnect_grace_ms,
                },
            )
            match.begin_disconnect_grace(
                color,
                on_expire=self._on_grace_expired,
                grace_ms=self._disconnect_grace_ms,
            )
            return

        was_spectator = session.role == SessionRole.SPECTATOR
        room_id = match.room_id
        match.release(websocket)
        if was_spectator and room_id is not None and session.user_id is not None:
            self._rooms.remove_user(room_id, session.user_id)
            logger.info(
                "spectator left room_id=%s game_id=%s user_id=%s",
                room_id,
                match.game_id,
                session.user_id,
            )
            await self._broadcast_room_update(match)

    async def discard_incomplete_match(self, match, websocket, session):
        """Close a waiting/solo room so the code cannot be joined after creator leave."""
        room_id = match.room_id
        game_id = match.game_id
        match.release(websocket)
        if room_id is not None:
            self._rooms.discard(room_id)
            logger.info(
                "waiting room discarded room_id=%s game_id=%s user_id=%s",
                room_id,
                game_id,
                session.user_id,
            )
        if game_id != self._default_game_id:
            await match.stop()
            self._registry.unregister(game_id)

    async def try_restore_disconnected_game(self, session):
        """If this user has a disconnected seat, restore it and send snapshot."""
        for match in self._registry.all_matches():
            color = match.reconnect_user(session, session.user_id)
            if color is None:
                continue

            opponent = "b" if color == "w" else "w"
            opp_session = match.player_for_color(opponent)
            await match.broadcast_message(
                "player_reconnected",
                payload={"color": color},
            )
            await session.websocket.send(
                encode_match_found(
                    game_id=match.game_id,
                    color=color,
                    opponent_username=(
                        opp_session.username if opp_session else ""
                    ),
                    opponent_rating=(
                        opp_session.rating if opp_session else 1200
                    ),
                )
            )
            await session.websocket.send(
                encode_message(
                    "state_snapshot",
                    payload=match.snapshot_payload(),
                )
            )
            return True
        return False
