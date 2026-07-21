import hashlib
import hmac
import secrets

from shared.protocol import (
    INVALID_CREDENTIALS,
    INVALID_USERNAME,
    ProtocolError,
    USERNAME_TAKEN,
    normalize_username,
)


PASSWORD_MIN_LENGTH = 4
_HASH_PREFIX = "pbkdf2_sha256"
_HASH_ITERATIONS = 100_000


class AuthError(Exception):
    """Raised when registration or login fails."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


def hash_password(password):
    """Return a salted PBKDF2 password hash string (never store plaintext)."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _HASH_ITERATIONS,
    )
    return f"{_HASH_PREFIX}${_HASH_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password, password_hash):
    """Return True when password matches the stored hash."""
    try:
        algorithm, iterations_text, salt, expected_hex = password_hash.split(
            "$", 3
        )
    except ValueError:
        return False
    if algorithm != _HASH_PREFIX:
        return False
    try:
        iterations = int(iterations_text)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return hmac.compare_digest(digest.hex(), expected_hex)


def validate_password(password):
    if not isinstance(password, str):
        raise AuthError(INVALID_CREDENTIALS, "password must be a string")
    if len(password) < PASSWORD_MIN_LENGTH:
        raise AuthError(
            INVALID_CREDENTIALS,
            f"password must be at least {PASSWORD_MIN_LENGTH} characters",
        )


class AuthService:
    """
    Registration and login against UserRepository.

    WebSocket handlers must call this instead of checking passwords themselves.
    """

    def __init__(self, user_repository):
        self._users = user_repository

    def register(self, username, password):
        try:
            username = normalize_username(username)
        except ProtocolError as exc:
            raise AuthError(INVALID_USERNAME, str(exc)) from exc

        validate_password(password)

        if self._users.get_by_username(username) is not None:
            raise AuthError(USERNAME_TAKEN, "username already registered")

        password_hash = hash_password(password)
        return self._users.create(username, password_hash=password_hash)

    def login(self, username, password):
        try:
            username = normalize_username(username)
        except ProtocolError as exc:
            raise AuthError(INVALID_USERNAME, str(exc)) from exc

        if not isinstance(password, str):
            raise AuthError(INVALID_CREDENTIALS, "invalid username or password")

        user = self._users.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthError(INVALID_CREDENTIALS, "invalid username or password")
        return user
