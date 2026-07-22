import argparse
import logging
import os
import sys

from client.startup_window import run_startup_window
from input.controller import Controller
from server.config import DEFAULT_HOST, DEFAULT_PORT
from view.factory import create_ui
from view.game_runner import GameRunner, get_work_area


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_remote_ui(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """
    Keep the application open: game → lobby → game …

    Closing the StartupWindow (Esc / window close without play) exits the app.
    Exit Game, game over, and connection loss all return to StartupWindow.
    """
    while True:
        result = run_startup_window(host, port)
        if result is None:
            return 2

        session = result.session
        window_width, window_height = get_work_area()
        ui = create_ui(window_width, window_height)
        controller = Controller(session, ui.board_mapper)
        runner = GameRunner(
            session=session,
            controller=controller,
            renderer=ui.renderer,
            window_name=f"KFChess Remote {os.getpid()}",
            exit_button_rect=ui.layout.exit_button_rect,
        )

        try:
            runner.run()
        finally:
            session.stop()

        if getattr(session, "connection_lost", False):
            logger.warning(
                "connection lost — returning to lobby: %s",
                getattr(session, "connection_lost_message", "Connection lost"),
            )
        elif runner.return_to_lobby:
            logger.info("returning to startup/lobby")
        else:
            # Unexpected exit path — still keep the app open.
            logger.info("game window closed — returning to startup/lobby")


def main(argv=None):
    parser = argparse.ArgumentParser(description="KFChess remote OpenCV client")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    raise SystemExit(run_remote_ui(host=args.host, port=args.port))


if __name__ == "__main__":
    main(sys.argv[1:])
