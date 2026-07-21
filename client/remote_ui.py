import argparse
import os
import sys

from client.remote_session import RemoteSession
from input.controller import Controller
from server.config import DEFAULT_HOST, DEFAULT_PORT
from view.factory import create_ui
from view.game_runner import GameRunner, get_work_area


def run_remote_ui(host=DEFAULT_HOST, port=DEFAULT_PORT):
    uri = f"ws://{host}:{port}"
    session = RemoteSession(uri)
    session.start()

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


def main(argv=None):
    parser = argparse.ArgumentParser(description="KFChess remote OpenCV client")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    run_remote_ui(host=args.host, port=args.port)


if __name__ == "__main__":
    main(sys.argv[1:])
