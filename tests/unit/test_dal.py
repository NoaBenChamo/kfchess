import pytest

from server.dal.database import Database
from server.dal.repositories import GameRepository, UserRepository


@pytest.fixture
def db():
    with Database(":memory:") as database:
        yield database


@pytest.fixture
def users(db):
    return UserRepository(db)


@pytest.fixture
def games(db):
    return GameRepository(db)


def test_create_and_get_user_by_username(users):
    created = users.create("Noa", password_hash="hash-noa")

    assert created.id is not None
    assert created.username == "Noa"
    assert created.password_hash == "hash-noa"
    assert created.rating == 1200
    assert created.created_at

    loaded = users.get_by_username("Noa")
    assert loaded == created
    assert users.get_by_id(created.id) == created


def test_duplicate_username_is_rejected(users):
    users.create("Noa", password_hash="hash-1")

    with pytest.raises(Exception):
        users.create("Noa", password_hash="hash-2")


def test_update_rating(users):
    user = users.create("Noa", password_hash="hash-noa")

    updated = users.update_rating(user.id, 1250)

    assert updated.rating == 1250
    assert users.get_by_id(user.id).rating == 1250


def test_update_rating_unknown_user_returns_none(users):
    assert users.update_rating(999, 1300) is None


def test_create_game_and_finish(users, games):
    white = users.create("Alice", password_hash="a")
    black = users.create("Bob", password_hash="b")

    game = games.create(white.id, black.id)

    assert game.white_user_id == white.id
    assert game.black_user_id == black.id
    assert game.winner_color is None
    assert game.ended_at is None

    finished = games.finish(game.id, winner_color="w")

    assert finished.winner_color == "w"
    assert finished.ended_at is not None
    assert games.get_by_id(game.id) == finished


def test_rating_changes_for_game(users, games):
    white = users.create("Alice", password_hash="a", rating=1200)
    black = users.create("Bob", password_hash="b", rating=1200)
    game = games.create(white.id, black.id)

    change_w = games.add_rating_change(game.id, white.id, 1200, 1216)
    change_b = games.add_rating_change(game.id, black.id, 1200, 1184)

    assert change_w.rating_before == 1200
    assert change_w.rating_after == 1216
    assert change_b.user_id == black.id

    listed = games.list_rating_changes(game.id)
    assert listed == [change_w, change_b]


def test_duplicate_rating_change_for_same_user_game_is_rejected(users, games):
    white = users.create("Alice", password_hash="a")
    black = users.create("Bob", password_hash="b")
    game = games.create(white.id, black.id)
    games.add_rating_change(game.id, white.id, 1200, 1216)

    with pytest.raises(Exception):
        games.add_rating_change(game.id, white.id, 1216, 1230)


def test_transaction_rolls_back_on_error(db, users):
    users.create("Keep", password_hash="k")

    with pytest.raises(RuntimeError):
        with db.transaction() as conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, rating, created_at)
                VALUES (?, ?, ?, ?)
                """,
                ("Temp", "t", 1200, "2020-01-01T00:00:00+00:00"),
            )
            raise RuntimeError("boom")

    assert users.get_by_username("Keep") is not None
    assert users.get_by_username("Temp") is None
