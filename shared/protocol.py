import json
import re


class ProtocolError(ValueError):
    """Raised when a network message cannot be decoded or is invalid."""


# Stage C/D/F error codes (and shared protocol codes).
INVALID_MESSAGE = "INVALID_MESSAGE"
INVALID_USERNAME = "INVALID_USERNAME"
INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
SERVER_FULL = "SERVER_FULL"
USERNAME_TAKEN = "USERNAME_TAKEN"
NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
NOT_YOUR_PIECE = "NOT_YOUR_PIECE"
NOT_IN_GAME = "NOT_IN_GAME"
MATCHMAKING_TIMEOUT = "MATCHMAKING_TIMEOUT"
ROOM_NOT_FOUND = "ROOM_NOT_FOUND"
SPECTATOR_READ_ONLY = "SPECTATOR_READ_ONLY"

USERNAME_MAX_LENGTH = 32
PASSWORD_MIN_LENGTH = 4
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
    elif message_type == "jump_request":
        payload = _validate_jump_payload(payload)
    elif message_type == "identify":
        payload = _validate_identify_payload(payload)
    elif message_type in ("register", "login"):
        payload = _validate_auth_payload(payload)
    elif message_type == "join_room":
        payload = _validate_join_room_payload(payload)

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


def _validate_jump_payload(payload):
    for key in ("row", "col"):
        if key not in payload:
            raise ProtocolError(f"jump_request payload requires {key}")
        if not isinstance(payload[key], int):
            raise ProtocolError(f"jump_request {key} must be an integer")
        if payload[key] < 0 or payload[key] > 7:
            raise ProtocolError(f"jump_request {key} out of range")
    return payload


def _validate_identify_payload(payload):
    if "username" not in payload:
        raise ProtocolError("identify payload requires username")
    normalized = normalize_username(payload["username"])
    return {**payload, "username": normalized}


def _validate_auth_payload(payload):
    if "username" not in payload:
        raise ProtocolError("auth payload requires username")
    if "password" not in payload:
        raise ProtocolError("auth payload requires password")
    if not isinstance(payload["password"], str):
        raise ProtocolError("password must be a string")
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


def encode_auth_ok(user_id, username, rating):
    """Encode a Stage D auth_ok response after register or login."""
    return encode_message(
        "auth_ok",
        payload={
            "user_id": user_id,
            "username": username,
            "rating": rating,
        },
    )


def encode_game_over(winner_color, reason, ratings=None, rated=False, game_id=None):
    """Encode a Stage D.3 game_over notification with optional rating updates."""
    payload = {
        "winner": winner_color,
        "reason": reason,
        "rated": bool(rated),
        "ratings": ratings or {},
    }
    if game_id is not None:
        payload["game_id"] = game_id
    return encode_message("game_over", payload=payload)


def encode_match_found(game_id, color, opponent_username, opponent_rating):
    """Encode Stage E match_found after successful matchmaking."""
    if color not in ("w", "b"):
        raise ProtocolError("color must be 'w' or 'b'")
    return encode_message(
        "match_found",
        payload={
            "game_id": game_id,
            "color": color,
            "opponent": {
                "username": opponent_username,
                "rating": opponent_rating,
            },
        },
        game_id=game_id,
    )


def encode_matchmaking_timeout():
    return encode_message("matchmaking_timeout", payload={})


def encode_player_disconnected(color, grace_period_ms):
    return encode_message(
        "player_disconnected",
        payload={
            "color": color,
            "grace_period_ms": grace_period_ms,
        },
    )


def encode_player_reconnected(color):
    return encode_message(
        "player_reconnected",
        payload={"color": color},
    )


def encode_room_update(
    room_id,
    game_id,
    players,
    spectators,
    status,
    role=None,
    color=None,
):
    """Encode Stage F room_update (membership + optional self role/color)."""
    payload = {
        "room_id": room_id,
        "game_id": game_id,
        "players": players,
        "spectators": spectators,
        "status": status,
    }
    if role is not None:
        payload["role"] = role
    if color is not None:
        payload["color"] = color
    return encode_message("room_update", payload=payload, game_id=game_id)


def _validate_join_room_payload(payload):
    if "room_id" not in payload:
        raise ProtocolError("join_room payload requires room_id")
    room_id = payload["room_id"]
    if not isinstance(room_id, str):
        raise ProtocolError("room_id must be a string")
    normalized = room_id.strip().upper()
    if not normalized:
        raise ProtocolError("room_id must be non-empty")
    return {**payload, "room_id": normalized}
