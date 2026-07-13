from board_io.board_parser import BoardParser
from input.controller import Controller
from engine.game_engine import GameEngine
from texttests.script_parser import ScriptParser
from texttests.script_runner import ScriptRunner


def main():
    lines = []

    while True:
        try:
            line = input()
            lines.append(line)

        except EOFError:
            break

    try:
        board = BoardParser.parse(lines)

    except ValueError as e:
        print(f"ERROR {e}")
        return


    game_engine = GameEngine(board)

    controller = Controller(game_engine)

    commands = ScriptParser.parse(lines)

    ScriptRunner(controller).run(commands)


if __name__ == "__main__":
    main()