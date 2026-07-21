import sqlite3
from contextlib import contextmanager
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rating INTEGER NOT NULL DEFAULT 1200,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    white_user_id INTEGER NOT NULL REFERENCES users(id),
    black_user_id INTEGER NOT NULL REFERENCES users(id),
    winner_color TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS rating_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    rating_before INTEGER NOT NULL,
    rating_after INTEGER NOT NULL,
    UNIQUE(game_id, user_id)
);
"""


class Database:
    """
    Thin SQLite access layer: connection, schema, and transactions.

    SQL stays in the DAL — callers use repositories, not raw SQL.
    """

    def __init__(self, path=":memory:"):
        self._path = path
        self._conn = None

    @property
    def connection(self):
        if self._conn is None:
            raise RuntimeError("database is not connected")
        return self._conn

    def connect(self):
        if self._conn is not None:
            return self

        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(
            self._path,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        return self

    def close(self):
        if self._conn is None:
            return
        self._conn.close()
        self._conn = None

    def initialize_schema(self):
        self.connection.executescript(SCHEMA_SQL)
        self.connection.commit()

    @contextmanager
    def transaction(self):
        """
        Commit on success, roll back on error.

        Nested usage shares the same connection transaction.
        """
        conn = self.connection
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def __enter__(self):
        self.connect()
        self.initialize_schema()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
