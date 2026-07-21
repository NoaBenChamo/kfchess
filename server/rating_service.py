from server.elo import calculate_new_ratings


class RatingService:
    """
    Starts and finalizes rated games.

    Does not know about WebSockets — only repositories and ELO math.
    """

    def __init__(self, user_repository, game_repository):
        self._users = user_repository
        self._games = game_repository

    def start_game(self, white_user_id, black_user_id):
        return self._games.create(white_user_id, black_user_id)

    def finalize_game(self, game_id, winner_color, rated=True):
        """
        Persist game result. Rated games update ELO exactly once.

        Args:
            game_id: SQLite games.id
            winner_color: "w", "b", or None for draw
            rated: when False, only mark the game finished

        Returns:
            dict with winner_color, rated, and per-color rating info
        """
        game = self._games.get_by_id(game_id)
        if game is None:
            raise ValueError(f"unknown game_id: {game_id}")

        existing = self._games.list_rating_changes(game_id)
        if existing:
            return self._result_from_existing(game, existing)

        result_code = winner_color if winner_color in ("w", "b") else "d"

        if not rated:
            finished = self._games.finish(game_id, winner_color)
            return {
                "game_id": game_id,
                "winner_color": finished.winner_color,
                "rated": False,
                "ratings": {},
            }

        white = self._users.get_by_id(game.white_user_id)
        black = self._users.get_by_id(game.black_user_id)
        if white is None or black is None:
            raise ValueError("missing players for rated game")

        new_white, new_black = calculate_new_ratings(
            white.rating,
            black.rating,
            result_code,
        )

        status = self._games.apply_rated_finish(
            game_id=game_id,
            winner_color=winner_color,
            white_user_id=white.id,
            black_user_id=black.id,
            white_before=white.rating,
            white_after=new_white,
            black_before=black.rating,
            black_after=new_black,
        )
        if status == "already":
            finished = self._games.get_by_id(game_id)
            changes = self._games.list_rating_changes(game_id)
            return self._result_from_existing(finished, changes)

        return {
            "game_id": game_id,
            "winner_color": winner_color,
            "rated": True,
            "ratings": {
                "w": {
                    "user_id": white.id,
                    "rating_before": white.rating,
                    "rating_after": new_white,
                },
                "b": {
                    "user_id": black.id,
                    "rating_before": black.rating,
                    "rating_after": new_black,
                },
            },
        }

    def _result_from_existing(self, game, changes):
        by_user = {change.user_id: change for change in changes}
        white_change = by_user.get(game.white_user_id)
        black_change = by_user.get(game.black_user_id)
        ratings = {}
        if white_change is not None:
            ratings["w"] = {
                "user_id": white_change.user_id,
                "rating_before": white_change.rating_before,
                "rating_after": white_change.rating_after,
            }
        if black_change is not None:
            ratings["b"] = {
                "user_id": black_change.user_id,
                "rating_before": black_change.rating_before,
                "rating_after": black_change.rating_after,
            }
        return {
            "game_id": game.id,
            "winner_color": game.winner_color,
            "rated": True,
            "ratings": ratings,
        }
