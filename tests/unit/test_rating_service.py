from server.auth_service import AuthService
from server.dal.database import Database
from server.dal.repositories import GameRepository, UserRepository
from server.rating_service import RatingService


def _services():
    database = Database(":memory:")
    database.connect()
    database.initialize_schema()
    users = UserRepository(database)
    games = GameRepository(database)
    auth = AuthService(users)
    rating = RatingService(users, games)
    return auth, rating, users, games, database


def test_finalize_rated_game_updates_both_players_once():
    auth, rating, users, games, _db = _services()
    white = auth.register("Alice", "secret1")
    black = auth.register("Bob", "secret1")
    # Give black a higher rating so white gains more than 16 on win.
    users.update_rating(black.id, 1400)
    black = users.get_by_id(black.id)

    game = rating.start_game(white.id, black.id)
    first = rating.finalize_game(game.id, winner_color="w", rated=True)

    assert first["rated"] is True
    assert first["winner_color"] == "w"
    assert first["ratings"]["w"]["rating_after"] > white.rating
    assert first["ratings"]["b"]["rating_after"] < black.rating

    white_after = users.get_by_id(white.id).rating
    black_after = users.get_by_id(black.id).rating
    assert white_after == first["ratings"]["w"]["rating_after"]
    assert black_after == first["ratings"]["b"]["rating_after"]

    second = rating.finalize_game(game.id, winner_color="w", rated=True)
    assert second["ratings"]["w"]["rating_after"] == white_after
    assert second["ratings"]["b"]["rating_after"] == black_after
    assert users.get_by_id(white.id).rating == white_after
    assert len(games.list_rating_changes(game.id)) == 2


def test_unrated_game_does_not_change_elo():
    auth, rating, users, _games, _db = _services()
    white = auth.register("Alice", "secret1")
    black = auth.register("Bob", "secret1")
    game = rating.start_game(white.id, black.id)

    result = rating.finalize_game(game.id, winner_color="w", rated=False)

    assert result["rated"] is False
    assert result["ratings"] == {}
    assert users.get_by_id(white.id).rating == 1200
    assert users.get_by_id(black.id).rating == 1200
