from server.room_manager import (
    STATUS_PLAYING,
    STATUS_WAITING,
    RoomManager,
)
from shared.protocol import ROOM_NOT_FOUND


def test_create_assigns_unique_room_id_and_white():
    ids = iter(["AAAAAA", "AAAAAA", "BBBBBB"])
    manager = RoomManager(id_factory=lambda: next(ids))

    room = manager.create("g1", creator_user_id=1)
    assert room.room_id == "AAAAAA"
    assert room.match_id == "g1"
    assert room.white_user_id == 1
    assert room.black_user_id is None
    assert room.status == STATUS_WAITING

    room2 = manager.create("g2", creator_user_id=2)
    assert room2.room_id == "BBBBBB"


def test_second_join_is_black_third_is_spectator():
    manager = RoomManager(id_factory=lambda: "ROOM01")
    manager.create("g1", creator_user_id=1)

    black = manager.join("ROOM01", user_id=2)
    assert black == {"ok": True, "role": "player", "color": "b"}
    room = manager.get("room01")
    assert room.black_user_id == 2
    assert room.status == STATUS_PLAYING

    spectator = manager.join("ROOM01", user_id=3)
    assert spectator == {"ok": True, "role": "spectator", "color": None}
    assert room.spectator_user_ids == [3]


def test_join_missing_room_returns_not_found():
    manager = RoomManager()
    result = manager.join("NOPE12", user_id=9)
    assert result["ok"] is False
    assert result["error_code"] == ROOM_NOT_FOUND
