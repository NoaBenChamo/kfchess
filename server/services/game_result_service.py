"""End-of-match result recording and rated-game start."""

import logging

logger = logging.getLogger(__name__)


class GameResultService:
    """Start rated games and finalize results exactly once."""

    def __init__(self, rating_service, rooms):
        self._rating = rating_service
        self._rooms = rooms

    def maybe_start_rated_game(self, match):
        if match.db_game_id is not None:
            return
        if match.player_count() != 2:
            return
        white = match.player_for_color("w")
        black = match.player_for_color("b")
        if (
            white is None
            or black is None
            or white.user_id is None
            or black.user_id is None
        ):
            return
        game = self._rating.start_game(white.user_id, black.user_id)
        match.db_game_id = game.id
        match.rated = True

    async def finalize_game_over(self, match):
        if match.is_result_recorded():
            return

        winner = match.detect_winner_color()
        if match.disconnect_forfeit:
            reason = "disconnect"
        elif winner is not None:
            reason = "king_captured"
        else:
            reason = "game_over"
        logger.info(
            "game ended game_id=%s room_id=%s winner=%s reason=%s",
            match.game_id,
            match.room_id,
            winner,
            reason,
        )

        if match.db_game_id is None:
            match.mark_result_recorded()
            await match.broadcast_message(
                "game_over",
                payload={
                    "winner": winner,
                    "reason": reason,
                    "rated": False,
                    "ratings": {},
                },
            )
            if match.room_id is not None:
                self._rooms.mark_finished(match.game_id)
            match.leave_all_players()
            return

        result = self._rating.finalize_game(
            match.db_game_id,
            winner,
            rated=match.rated,
        )
        match.mark_result_recorded()

        for color, info in result.get("ratings", {}).items():
            session = match.player_for_color(color)
            if session is not None:
                session.rating = info["rating_after"]

        await match.broadcast_message(
            "game_over",
            payload={
                "winner": result["winner_color"],
                "reason": reason,
                "rated": result["rated"],
                "ratings": result["ratings"],
                "game_id": result["game_id"],
            },
        )
        if match.room_id is not None:
            self._rooms.mark_finished(match.game_id)
        match.leave_all_players()

    async def on_grace_expired(self, match, color):
        async with match.lock:
            seated = match.player_for_color(color)
            if seated is None or not seated.disconnected:
                return
            if match.engine.is_game_over():
                return
            match.engine.resign(color)
            match.disconnect_forfeit = True

        await match.broadcast_snapshot()
        await self.finalize_game_over(match)
