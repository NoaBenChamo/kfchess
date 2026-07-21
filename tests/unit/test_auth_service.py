from server.auth_service import (
    AuthError,
    AuthService,
    hash_password,
    verify_password,
)
from server.dal.database import Database
from server.dal.repositories import UserRepository
from shared.protocol import INVALID_CREDENTIALS, USERNAME_TAKEN


def _auth_service():
    database = Database(":memory:")
    database.connect()
    database.initialize_schema()
    return AuthService(UserRepository(database)), database


def test_register_creates_user_with_rating_1200():
    auth, _db = _auth_service()

    user = auth.register("Noa", "secret1")

    assert user.username == "Noa"
    assert user.rating == 1200
    assert user.password_hash != "secret1"
    assert verify_password("secret1", user.password_hash)


def test_register_duplicate_username_is_rejected():
    auth, _db = _auth_service()
    auth.register("Noa", "secret1")

    try:
        auth.register("Noa", "other-pass")
        assert False, "expected AuthError"
    except AuthError as exc:
        assert exc.code == USERNAME_TAKEN


def test_login_success():
    auth, _db = _auth_service()
    auth.register("Noa", "secret1")

    user = auth.login("Noa", "secret1")

    assert user.username == "Noa"
    assert user.rating == 1200


def test_login_wrong_password_is_rejected():
    auth, _db = _auth_service()
    auth.register("Noa", "secret1")

    try:
        auth.login("Noa", "wrong")
        assert False, "expected AuthError"
    except AuthError as exc:
        assert exc.code == INVALID_CREDENTIALS


def test_login_unknown_user_is_rejected():
    auth, _db = _auth_service()

    try:
        auth.login("Ghost", "secret1")
        assert False, "expected AuthError"
    except AuthError as exc:
        assert exc.code == INVALID_CREDENTIALS


def test_hash_password_differs_from_plaintext():
    hashed = hash_password("secret1")
    assert hashed != "secret1"
    assert hashed.startswith("pbkdf2_sha256$")
