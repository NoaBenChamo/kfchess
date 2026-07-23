import secrets
import string

from server.session_role_enum import SessionRole


ROOM_ID_ALPHABET = string.ascii_uppercase + string.digits
ROOM_ID_LENGTH = 6

STATUS_WAITING = "waiting"
STATUS_PLAYING = "playing"
STATUS_FINISHED = "finished"


class Room:
    """Private match lobby keyed by a short room_id."""

    def __init__(self, room_id, match_id):
        self.room_id = room_id
        self.match_id = match_id
        self.white_user_id = None
        self.black_user_id = None
        self.spectator_user_ids = []
        self.status = STATUS_WAITING

    def seat_count(self):
        return sum(
            1
            for user_id in (self.white_user_id, self.black_user_id)
            if user_id is not None
        )


class RoomManager:
    """
    Owns room membership metadata (room_id → match_id / seats / status).

    Player/spectator sockets and broadcast live on Match; this registry only
    tracks lobby membership for create/join routing.
    """

    def __init__(self, id_factory=None):
        self._rooms = {}
        self._by_match = {}
        self._id_factory = id_factory or self._generate_room_id

    def create(self, match_id, creator_user_id):
        room_id = self._id_factory()
        while room_id in self._rooms:
            room_id = self._id_factory()

        room = Room(room_id, match_id)
        room.white_user_id = creator_user_id
        room.status = STATUS_WAITING
        self._rooms[room_id] = room
        self._by_match[match_id] = room_id
        return room

    def get(self, room_id):
        if room_id is None:
            return None
        return self._rooms.get(str(room_id).strip().upper())

    def get_by_match(self, match_id):
        room_id = self._by_match.get(match_id)
        if room_id is None:
            return None
        return self._rooms.get(room_id)

    def join(self, room_id, user_id):
        """
        Assign join role for an authenticated user.

        Returns:
            {"ok": True, "role": SessionRole.PLAYER|SessionRole.SPECTATOR, "color": "w"|"b"|None}
            or {"ok": False, "error_code": ..., "error_message": ...}
        """
        from shared.protocol import INVALID_MESSAGE, ROOM_NOT_FOUND

        room = self.get(room_id)
        if room is None or room.status == STATUS_FINISHED:
            return {
                "ok": False,
                "error_code": ROOM_NOT_FOUND,
                "error_message": "room not found",
            }

        if user_id in (
            room.white_user_id,
            room.black_user_id,
            *room.spectator_user_ids,
        ):
            return {
                "ok": False,
                "error_code": INVALID_MESSAGE,
                "error_message": "already in this room",
            }

        if room.white_user_id is None:
            room.white_user_id = user_id
            room.status = STATUS_WAITING
            return {"ok": True, "role": SessionRole.PLAYER, "color": "w"}

        if room.black_user_id is None:
            room.black_user_id = user_id
            room.status = STATUS_PLAYING
            return {"ok": True, "role": SessionRole.PLAYER, "color": "b"}

        room.spectator_user_ids.append(user_id)
        return {"ok": True, "role": SessionRole.SPECTATOR, "color": None}

    def remove_user(self, room_id, user_id):
        room = self.get(room_id)
        if room is None:
            return
        if room.white_user_id == user_id:
            room.white_user_id = None
        if room.black_user_id == user_id:
            room.black_user_id = None
        room.spectator_user_ids = [
            uid for uid in room.spectator_user_ids if uid != user_id
        ]
        if room.seat_count() < 2 and room.status == STATUS_PLAYING:
            room.status = STATUS_WAITING

    def mark_finished(self, match_id):
        room = self.get_by_match(match_id)
        if room is None:
            return
        room.status = STATUS_FINISHED

    def discard(self, room_id):
        room = self._rooms.pop(str(room_id).strip().upper(), None)
        if room is not None:
            self._by_match.pop(room.match_id, None)

    def _generate_room_id(self):
        return "".join(
            secrets.choice(ROOM_ID_ALPHABET) for _ in range(ROOM_ID_LENGTH)
        )
