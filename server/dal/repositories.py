from dataclasses import dataclass
from datetime import datetime, timezone


def _utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class User:
    id: int
    username: str
    password_hash: str
    rating: int
    created_at: str


@dataclass(frozen=True)
class Game:
    id: int
    white_user_id: int
    black_user_id: int
    winner_color: str | None
    started_at: str
    ended_at: str | None


@dataclass(frozen=True)
class RatingChange:
    id: int
    game_id: int
    user_id: int
    rating_before: int
    rating_after: int


def _user_from_row(row):
    if row is None:
        return None
    return User(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
        rating=row["rating"],
        created_at=row["created_at"],
    )


def _game_from_row(row):
    if row is None:
        return None
    return Game(
        id=row["id"],
        white_user_id=row["white_user_id"],
        black_user_id=row["black_user_id"],
        winner_color=row["winner_color"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
    )


def _rating_change_from_row(row):
    if row is None:
        return None
    return RatingChange(
        id=row["id"],
        game_id=row["game_id"],
        user_id=row["user_id"],
        rating_before=row["rating_before"],
        rating_after=row["rating_after"],
    )


class UserRepository:
    """Persistence for users. Returns User DTOs, never cursors."""

    def __init__(self, database):
        self._db = database

    def create(self, username, password_hash, rating=1200, created_at=None):
        created_at = created_at or _utc_now_iso()
        with self._db.transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (username, password_hash, rating, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (username, password_hash, rating, created_at),
            )
            user_id = cursor.lastrowid
        return self.get_by_id(user_id)

    def get_by_id(self, user_id):
        row = self._db.connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return _user_from_row(row)

    def get_by_username(self, username):
        row = self._db.connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return _user_from_row(row)

    def update_rating(self, user_id, rating):
        with self._db.transaction() as conn:
            cursor = conn.execute(
                "UPDATE users SET rating = ? WHERE id = ?",
                (rating, user_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_by_id(user_id)


class GameRepository:
    """Persistence for games and rating_changes. Returns DTOs, never cursors."""

    def __init__(self, database):
        self._db = database

    def create(self, white_user_id, black_user_id, started_at=None):
        started_at = started_at or _utc_now_iso()
        with self._db.transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO games (
                    white_user_id, black_user_id, winner_color, started_at, ended_at
                )
                VALUES (?, ?, NULL, ?, NULL)
                """,
                (white_user_id, black_user_id, started_at),
            )
            game_id = cursor.lastrowid
        return self.get_by_id(game_id)

    def get_by_id(self, game_id):
        row = self._db.connection.execute(
            "SELECT * FROM games WHERE id = ?",
            (game_id,),
        ).fetchone()
        return _game_from_row(row)

    def finish(self, game_id, winner_color, ended_at=None):
        ended_at = ended_at or _utc_now_iso()
        with self._db.transaction() as conn:
            cursor = conn.execute(
                """
                UPDATE games
                SET winner_color = ?, ended_at = ?
                WHERE id = ?
                """,
                (winner_color, ended_at, game_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_by_id(game_id)

    def add_rating_change(self, game_id, user_id, rating_before, rating_after):
        with self._db.transaction() as conn:
            cursor = conn.execute(
                """
                INSERT INTO rating_changes (
                    game_id, user_id, rating_before, rating_after
                )
                VALUES (?, ?, ?, ?)
                """,
                (game_id, user_id, rating_before, rating_after),
            )
            change_id = cursor.lastrowid
        row = self._db.connection.execute(
            "SELECT * FROM rating_changes WHERE id = ?",
            (change_id,),
        ).fetchone()
        return _rating_change_from_row(row)

    def list_rating_changes(self, game_id):
        rows = self._db.connection.execute(
            """
            SELECT * FROM rating_changes
            WHERE game_id = ?
            ORDER BY id ASC
            """,
            (game_id,),
        ).fetchall()
        return [_rating_change_from_row(row) for row in rows]

    def apply_rated_finish(
        self,
        game_id,
        winner_color,
        white_user_id,
        black_user_id,
        white_before,
        white_after,
        black_before,
        black_after,
        ended_at=None,
    ):
        """
        Atomically finish a rated game and update both ratings once.

        Returns:
            "applied" when written, "already" when rating_changes already exist.
        """
        ended_at = ended_at or _utc_now_iso()
        with self._db.transaction() as conn:
            existing = conn.execute(
                "SELECT id FROM rating_changes WHERE game_id = ? LIMIT 1",
                (game_id,),
            ).fetchone()
            if existing is not None:
                return "already"

            conn.execute(
                """
                UPDATE games
                SET winner_color = ?, ended_at = ?
                WHERE id = ?
                """,
                (winner_color, ended_at, game_id),
            )
            conn.execute(
                "UPDATE users SET rating = ? WHERE id = ?",
                (white_after, white_user_id),
            )
            conn.execute(
                "UPDATE users SET rating = ? WHERE id = ?",
                (black_after, black_user_id),
            )
            conn.execute(
                """
                INSERT INTO rating_changes (
                    game_id, user_id, rating_before, rating_after
                )
                VALUES (?, ?, ?, ?)
                """,
                (game_id, white_user_id, white_before, white_after),
            )
            conn.execute(
                """
                INSERT INTO rating_changes (
                    game_id, user_id, rating_before, rating_after
                )
                VALUES (?, ?, ?, ?)
                """,
                (game_id, black_user_id, black_before, black_after),
            )
        return "applied"
