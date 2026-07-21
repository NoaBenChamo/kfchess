import argparse
import getpass
import os
import sys

from client.remote_session import IdentifyError, RemoteSession
from input.controller import Controller
from server.config import DEFAULT_HOST, DEFAULT_PORT
from view.factory import create_ui
from view.game_runner import GameRunner, get_work_area


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

    uri = f"ws://{host}:{port}"
    session = RemoteSession(
        uri,
        username=username,
        password=password,
        auth_mode=auth_mode,
    )

    try:
        session.start()
    except IdentifyError as exc:
        print(f"auth/identify failed: {exc.code} — {exc.message}", file=sys.stderr)
        return 1
    except TimeoutError as exc:
        print(str(exc), file=sys.stderr)
        session.stop()
        return 1

    color = session.state.assigned_color
    rating = session.state.rating
    print(
        f"Joined as {session.state.username} ({color}), rating={rating}"
    )

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
    args = parser.parse_args(argv)
    raise SystemExit(
        run_remote_ui(
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
            auth_mode="register" if args.register else "login",
        )
    )


if __name__ == "__main__":
    main(sys.argv[1:])
