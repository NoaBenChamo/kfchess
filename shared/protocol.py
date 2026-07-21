import json
import re


class ProtocolError(ValueError):
    """Raised when a network message cannot be decoded or is invalid."""


# Stage C error codes (and shared protocol codes).
INVALID_MESSAGE = "INVALID_MESSAGE"
INVALID_USERNAME = "INVALID_USERNAME"
SERVER_FULL = "SERVER_FULL"
USERNAME_TAKEN = "USERNAME_TAKEN"
NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
NOT_YOUR_PIECE = "NOT_YOUR_PIECE"

USERNAME_MAX_LENGTH = 32
_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def normalize_username(username):
    """
    Strip and validate a username.

    Returns the normalized username string.
    Raises ProtocolError when the username is invalid.
    """
    if not isinstance(username, str):
        raise ProtocolError("username must be a string")

    normalized = username.strip()
    if not normalized:
        raise ProtocolError("username must be non-empty")
    if len(normalized) > USERNAME_MAX_LENGTH:
        raise ProtocolError(
            f"username must be at most {USERNAME_MAX_LENGTH} characters"
        )
    if not _USERNAME_PATTERN.fullmatch(normalized):
        raise ProtocolError(
            "username may only contain letters, digits, underscore, and hyphen"
        )
    return normalized


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

    Validates payload shape for ``move`` and ``identify``.
    For ``identify``, normalizes ``username`` (strip) into the returned payload.
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
    elif message_type == "identify":
        payload = _validate_identify_payload(payload)

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


def _validate_identify_payload(payload):
    if "username" not in payload:
        raise ProtocolError("identify payload requires username")
    normalized = normalize_username(payload["username"])
    return {**payload, "username": normalized}


def encode_error(code, message):
    return encode_message(
        "error",
        payload={"code": code, "message": message},
    )


def encode_identity_assigned(username, color, game_id="default"):
    """Encode a Stage C identity_assigned response."""
    if color not in ("w", "b"):
        raise ProtocolError("color must be 'w' or 'b'")
    return encode_message(
        "identity_assigned",
        payload={
            "username": username,
            "color": color,
            "game_id": game_id,
        },
    )
