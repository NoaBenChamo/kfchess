import argparse
import getpass
import logging
import os
import sys

from client.remote_session import IdentifyError, RemoteSession
from client.room_dialog import (
    MODE_CREATE_ROOM,
    MODE_JOIN_ROOM,
    MODE_MATCHMAKING,
    prompt_room_choice,
)
from input.controller import Controller
from server.config import DEFAULT_HOST, DEFAULT_PORT
from view.factory import create_ui
from view.game_runner import GameRunner, get_work_area


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def prompt_username():
    try:
        return input("Username: ").strip()
    except EOFError:
        return ""


def prompt_password():
    try:
        return getpass.getpass("Password: ")
    except EOFError:
        return ""


def run_remote_ui(
    host=DEFAULT_HOST,
    port=DEFAULT_PORT,
    username=None,
    password=None,
    auth_mode="login",
    play_mode=None,
    room_id=None,
):
    if username is None:
        username = prompt_username()
    if not username:
        print("username is required", file=sys.stderr)
        return 2

    if password is None:
        password = prompt_password()
    if not password:
        print("password is required", file=sys.stderr)
        return 2

    choice = prompt_room_choice(default_mode=play_mode, room_id=room_id)
    if choice is None:
        print("cancelled", file=sys.stderr)
        return 2

    uri = f"ws://{host}:{port}"
    session = RemoteSession(
        uri,
        username=username,
        password=password,
        auth_mode=auth_mode,
        play_mode=choice["mode"],
        room_id=choice["room_id"],
    )

    try:
        session.start()
    except IdentifyError as exc:
        logger.error("auth/play failed: %s — %s", exc.code, exc.message)
        print(f"auth/play failed: {exc.code} — {exc.message}", file=sys.stderr)
        return 1
    except TimeoutError as exc:
        logger.error("%s", exc)
        print(str(exc), file=sys.stderr)
        session.stop()
        return 1

    color = session.state.assigned_color or "-"
    role = session.state.role or "player"
    rating = session.state.rating
    game_id = session.state.game_id
    room = session.state.room_id
    print(
        f"Joined as {session.state.username} role={role} color={color}, "
        f"rating={rating}, game={game_id}"
        + (f", room={room}" if room else "")
    )
    if choice["mode"] == MODE_CREATE_ROOM and room:
        print(f"Share room code: {room}")

    window_width, window_height = get_work_area()
    ui = create_ui(window_width, window_height)
    controller = Controller(session, ui.board_mapper)
    runner = GameRunner(
        session=session,
        controller=controller,
        renderer=ui.renderer,
        window_name=f"KFChess Remote {os.getpid()}",
    )

    try:
        runner.run()
    finally:
        session.stop()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="KFChess remote OpenCV client")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--username", default=None)
    parser.add_argument(
        "--password",
        default=None,
        help="Prefer interactive prompt; flag is for local testing only",
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Register a new account instead of logging in",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--matchmaking",
        action="store_true",
        help="Skip dialog and join matchmaking",
    )
    mode.add_argument(
        "--create-room",
        action="store_true",
        help="Skip dialog and create a private room",
    )
    mode.add_argument(
        "--join-room",
        metavar="ROOM_ID",
        default=None,
        help="Skip dialog and join a private room",
    )
    args = parser.parse_args(argv)

    play_mode = None
    room_id = None
    if args.matchmaking:
        play_mode = MODE_MATCHMAKING
    elif args.create_room:
        play_mode = MODE_CREATE_ROOM
    elif args.join_room:
        play_mode = MODE_JOIN_ROOM
        room_id = args.join_room.strip().upper()

    raise SystemExit(
        run_remote_ui(
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
            auth_mode="register" if args.register else "login",
            play_mode=play_mode,
            room_id=room_id,
        )
    )


if __name__ == "__main__":
    main(sys.argv[1:])
