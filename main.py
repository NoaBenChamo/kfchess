from board_io.board_parser import BoardParser
from bus.events import GameStartedEvent, GameOverEvent
from engine.game_engine import GameEngine
from input.controller import Controller
from session.local_session import LocalSession
from view.audio.sound_player import SoundPlayer
from view.factory import create_ui
from view.game_runner import GameRunner, get_work_area
from view.hud.game_over_tracker import GameOverTracker


INITIAL_BOARD = """
Board:
bR bN bB bQ bK bB bN bR
bP bP bP bP bP bP bP bP
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
.  .  .  .  .  .  .  .
wP wP wP wP wP wP wP wP
wR wN wB wQ wK wB wN wR
"""


def create_game():
    """
    Creates and connects all game components.

    Returns:
        GameRunner: Fully configured game runner.
    """
    board = BoardParser.parse(
        INITIAL_BOARD.strip().splitlines()
    )

    engine = GameEngine(board)

    sound_player = SoundPlayer()
    game_over_tracker = GameOverTracker()
    engine.subscribe(GameStartedEvent, sound_player.on_game_started)
    engine.subscribe(GameOverEvent, sound_player.on_game_over)
    engine.subscribe(GameOverEvent, game_over_tracker.on_game_over)
    engine.start_game()

    window_width, window_height = get_work_area()
    ui = create_ui(window_width, window_height)

    session = LocalSession(engine)
    controller = Controller(
        session=session,
        board_mapper=ui.board_mapper,
    )

    return GameRunner(
        session=session,
        controller=controller,
        renderer=ui.renderer,
    )


def main():
    game_runner = create_game()
    game_runner.run()


if __name__ == "__main__":
    main()
