import json


class ProtocolError(ValueError):
    """Raised when a network message cannot be decoded or is invalid."""


def encode_message(message_type, payload=None, request_id=None, game_id=None):
    """
    Encode a protocol envelope as a JSON string.

    Envelope shape:
        {"type": "...", "payload": {}, ...optional fields...}
    """
    if not isinstance(message_type, str) or not message_type:
        raise ProtocolError("message type must be a non-empty string")

    message = {
        "type": message_type,
        "payload": {} if payload is None else payload,
    }
    if request_id is not None:
        message["request_id"] = request_id
    if game_id is not None:
        message["game_id"] = game_id

    return json.dumps(message)


def decode_message(raw):
    """
    Decode a JSON envelope into a dict with at least `type` and `payload`.

    For ``type == "move"``, validates that payload contains a string ``command``.
    Does not parse the chess command itself.
    """
    if not isinstance(raw, str):
        raise ProtocolError("message must be a string")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProtocolError("invalid json") from exc

    if not isinstance(data, dict):
        raise ProtocolError("message must be a json object")

    message_type = data.get("type")
    if not isinstance(message_type, str) or not message_type:
        raise ProtocolError("missing or invalid type")

    payload = data.get("payload", {})
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ProtocolError("payload must be an object")

    if message_type == "move":
        _validate_move_payload(payload)

    result = {
        "type": message_type,
        "payload": payload,
    }
    if "request_id" in data:
        result["request_id"] = data["request_id"]
    if "game_id" in data:
        result["game_id"] = data["game_id"]
    return result


def _validate_move_payload(payload):
    if "command" not in payload:
        raise ProtocolError("move payload requires command")
    if not isinstance(payload["command"], str):
        raise ProtocolError("move command must be a string")


def encode_error(code, message):
    return encode_message(
        "error",
        payload={"code": code, "message": message},
    )
