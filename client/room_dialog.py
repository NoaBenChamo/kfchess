"""Console room dialog shown before the remote OpenCV game window."""


MODE_MATCHMAKING = "matchmaking"
MODE_CREATE_ROOM = "create_room"
MODE_JOIN_ROOM = "join_room"


def prompt_room_choice(default_mode=None, room_id=None):
    """
    Ask how to enter a game.

    Returns:
        {"mode": MODE_*, "room_id": str|None}
    """
    if default_mode in (MODE_MATCHMAKING, MODE_CREATE_ROOM, MODE_JOIN_ROOM):
        if default_mode == MODE_JOIN_ROOM and not room_id:
            room_id = _prompt("Room ID: ").strip().upper()
        return {"mode": default_mode, "room_id": room_id}

    print()
    print("How do you want to play?")
    print("  1) Matchmaking (Play)")
    print("  2) Create private room")
    print("  3) Join private room")
    print("  4) Cancel")
    choice = _prompt("Choice [1-4]: ").strip()

    if choice == "1":
        return {"mode": MODE_MATCHMAKING, "room_id": None}
    if choice == "2":
        return {"mode": MODE_CREATE_ROOM, "room_id": None}
    if choice == "3":
        entered = _prompt("Room ID: ").strip().upper()
        if not entered:
            print("room id is required")
            return None
        return {"mode": MODE_JOIN_ROOM, "room_id": entered}
    return None


def _prompt(label):
    try:
        return input(label)
    except EOFError:
        return ""
