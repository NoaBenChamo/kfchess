"""Matchmaking queue and paired-game creation."""

import logging
import uuid

from shared.protocol import (
    INVALID_MESSAGE,
    NOT_AUTHENTICATED,
    encode_error,
    encode_match_found,
    encode_matchmaking_timeout,
    encode_message,
)

logger = logging.getLogger(__name__)


class MatchmakingHandler:
    """Enqueue players, expire waiters, and start rated paired matches."""

    def __init__(
        self,
        sessions,
        registry,
        matchmaker,
        *,
        create_match_fn,
        start_tick_if_running_fn,
        start_rated_fn,
    ):
        self._sessions = sessions
        self._registry = registry
        self._matchmaker = matchmaker
        self._create_match = create_match_fn
        self._start_tick_if_running = start_tick_if_running_fn
        self._start_rated = start_rated_fn

    async def handle_play_request(self, websocket, message):
        del message
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return
        if not session.is_authenticated:
            await websocket.send(
                encode_error(NOT_AUTHENTICATED, "login before play_request")
            )
            return
        if session.is_in_game or session.role is not None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "already in a game")
            )
            return

        for match in self._registry.all_matches():
            seated = match.player_for_color("w")
            if seated and seated.user_id == session.user_id:
                await websocket.send(
                    encode_error(INVALID_MESSAGE, "already in a game")
                )
                return
            seated = match.player_for_color("b")
            if seated and seated.user_id == session.user_id:
                await websocket.send(
                    encode_error(INVALID_MESSAGE, "already in a game")
                )
                return

        pair = self._matchmaker.enqueue(session)
        if pair is None:
            logger.info(
                "matchmaking waiting connection_id=%s user_id=%s rating=%s",
                session.connection_id,
                session.user_id,
                session.rating,
            )
            await websocket.send(
                encode_message("request_ok", payload={"status": "waiting"})
            )
            return

        earlier, newer = pair
        logger.info(
            "matchmaking matched user_ids=%s,%s",
            earlier.session.user_id,
            newer.session.user_id,
        )
        await self.start_matched_game(earlier.session, newer.session)

    async def handle_cancel_matchmaking(self, websocket, message):
        del message
        session = self._sessions.get(websocket)
        if session is None:
            await websocket.send(
                encode_error(INVALID_MESSAGE, "unknown connection")
            )
            return
        removed = self._matchmaker.cancel(session.connection_id)
        await websocket.send(
            encode_message(
                "request_ok",
                payload={"status": "cancelled" if removed else "not_waiting"},
            )
        )

    async def start_matched_game(self, white_session, black_session):
        game_id = f"g_{uuid.uuid4().hex[:12]}"
        match = self._create_match(game_id)
        self._registry.register(match)
        await self._start_tick_if_running(match)

        async with match.lock:
            white_result = match.try_assign_player(
                white_session, white_session.username
            )
            black_result = match.try_assign_player(
                black_session, black_session.username
            )

        if not white_result["ok"] or not black_result["ok"]:
            logger.error("failed to seat matched players into %s", game_id)
            return

        self._start_rated(match)

        logger.info(
            "game created game_id=%s white=%s black=%s",
            game_id,
            white_session.username,
            black_session.username,
        )

        await white_session.websocket.send(
            encode_match_found(
                game_id=game_id,
                color="w",
                opponent_username=black_session.username,
                opponent_rating=black_session.rating or 1200,
            )
        )
        await black_session.websocket.send(
            encode_match_found(
                game_id=game_id,
                color="b",
                opponent_username=white_session.username,
                opponent_rating=white_session.rating or 1200,
            )
        )

        snapshot = match.snapshot_payload()
        raw_snapshot = encode_message("state_snapshot", payload=snapshot)
        await white_session.websocket.send(raw_snapshot)
        await black_session.websocket.send(raw_snapshot)

    async def expire_matchmaking(self):
        for waiting in self._matchmaker.pop_expired():
            try:
                await waiting.session.websocket.send(encode_matchmaking_timeout())
            except Exception:
                logger.debug(
                    "failed to notify matchmaking timeout for %s",
                    waiting.connection_id,
                )

    async def timeout_loop(self, sleep_fn):
        """Background loop; ``sleep_fn`` is typically ``asyncio.sleep``."""
        while True:
            try:
                await sleep_fn(0.5)
                await self.expire_matchmaking()
            except Exception:
                logger.exception("matchmaking timeout loop error")
