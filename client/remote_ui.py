import argparse
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


def run_remote_ui(host=DEFAULT_HOST, port=DEFAULT_PORT, username=None):
    if username is None:
        username = prompt_username()
    if not username:
        print("username is required", file=sys.stderr)
        return 2

    uri = f"ws://{host}:{port}"
    session = RemoteSession(uri, username=username)

    try:
        session.start()
    except IdentifyError as exc:
        print(f"identify failed: {exc.code} — {exc.message}", file=sys.stderr)
        return 1
    except TimeoutError as exc:
        print(str(exc), file=sys.stderr)
        session.stop()
        return 1

    color = session.state.assigned_color
    print(f"Joined as {session.state.username} ({color})")

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
    parser.add_argument(
        "--username",
        default=None,
        help="Skip the Shell prompt and use this username",
    )
    args = parser.parse_args(argv)
    raise SystemExit(
        run_remote_ui(host=args.host, port=args.port, username=args.username)
    )


if __name__ == "__main__":
    main(sys.argv[1:])
