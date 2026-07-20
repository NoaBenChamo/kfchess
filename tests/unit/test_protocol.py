import pytest

from shared.protocol import (
    ProtocolError,
    decode_message,
    encode_error,
    encode_message,
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
