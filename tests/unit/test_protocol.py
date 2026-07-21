import pytest

from shared.protocol import (
    ProtocolError,
    USERNAME_MAX_LENGTH,
    decode_message,
    encode_error,
    encode_identity_assigned,
    encode_message,
    normalize_username,
)


def test_encode_and_decode_roundtrip():
    raw = encode_message("ping", payload={})
    message = decode_message(raw)

    assert message["type"] == "ping"
    assert message["payload"] == {}


def test_encode_includes_optional_fields():
    raw = encode_message(
        "ping",
        payload={},
        request_id="r1",
        game_id="default",
    )
    message = decode_message(raw)

    assert message["request_id"] == "r1"
    assert message["game_id"] == "default"


def test_decode_rejects_invalid_json():
    with pytest.raises(ProtocolError, match="invalid json"):
        decode_message("{not-json")


def test_decode_rejects_missing_type():
    with pytest.raises(ProtocolError, match="type"):
        decode_message('{"payload": {}}')


def test_decode_rejects_non_object_payload():
    with pytest.raises(ProtocolError, match="payload"):
        decode_message('{"type": "ping", "payload": []}')


def test_encode_error_shape():
    message = decode_message(encode_error("INVALID_MESSAGE", "bad"))
    assert message["type"] == "error"
    assert message["payload"]["code"] == "INVALID_MESSAGE"
    assert message["payload"]["message"] == "bad"


def test_move_encode_decode_roundtrip():
    raw = encode_message("move", payload={"command": "WQe2e5"})
    message = decode_message(raw)

    assert message["type"] == "move"
    assert message["payload"] == {"command": "WQe2e5"}


def test_move_without_command_is_rejected():
    with pytest.raises(ProtocolError, match="command"):
        decode_message('{"type": "move", "payload": {}}')


def test_move_with_non_string_command_is_rejected():
    with pytest.raises(ProtocolError, match="command must be a string"):
        decode_message('{"type": "move", "payload": {"command": 123}}')


def test_move_with_non_dict_payload_is_rejected():
    with pytest.raises(ProtocolError, match="payload must be an object"):
        decode_message('{"type": "move", "payload": "WQe2e5"}')


def test_identify_encode_decode_roundtrip_normalizes_username():
    raw = encode_message("identify", payload={"username": "  Noa  "})
    message = decode_message(raw)

    assert message["type"] == "identify"
    assert message["payload"]["username"] == "Noa"


def test_identify_without_username_is_rejected():
    with pytest.raises(ProtocolError, match="username"):
        decode_message('{"type": "identify", "payload": {}}')


def test_identify_empty_username_is_rejected():
    with pytest.raises(ProtocolError, match="non-empty"):
        decode_message('{"type": "identify", "payload": {"username": "   "}}')


def test_identify_non_string_username_is_rejected():
    with pytest.raises(ProtocolError, match="username must be a string"):
        decode_message('{"type": "identify", "payload": {"username": 123}}')


def test_identify_rejects_invalid_characters():
    with pytest.raises(ProtocolError, match="letters"):
        decode_message(
            '{"type": "identify", "payload": {"username": "bad name!"}}'
        )


def test_identify_rejects_too_long_username():
    too_long = "a" * (USERNAME_MAX_LENGTH + 1)
    with pytest.raises(ProtocolError, match="at most"):
        decode_message(
            f'{{"type": "identify", "payload": {{"username": "{too_long}"}}}}'
        )


def test_normalize_username_accepts_valid_names():
    assert normalize_username("Alice_1") == "Alice_1"
    assert normalize_username("bob-2") == "bob-2"


def test_encode_identity_assigned_shape():
    message = decode_message(
        encode_identity_assigned("Noa", "w", game_id="default")
    )
    assert message["type"] == "identity_assigned"
    assert message["payload"] == {
        "username": "Noa",
        "color": "w",
        "game_id": "default",
    }


def test_encode_identity_assigned_rejects_invalid_color():
    with pytest.raises(ProtocolError, match="color"):
        encode_identity_assigned("Noa", "x")
