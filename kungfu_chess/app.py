from kungfu_chess.io.board_parser import BoardParser
from kungfu_chess.io.board_validator import BoardValidator
from kungfu_chess.io.board_printer import BoardPrinter

from kungfu_chess.engine.game_engine import Game

from kungfu_chess.input.command_parser import CommandParser
from kungfu_chess.input.commands import (
    PrintBoardCommand,
    ClickCommand,
    WaitCommand,
)
from kungfu_chess.input.jump_command import JumpCommand


def read_input():

    lines = []

    while True:

        try:
            lines.append(input())

        except EOFError:
            break

    return lines


def main():

    lines = read_input()

    board = BoardParser.parse(lines)

    error = BoardValidator.validate(board)

    if error:
        print(error)
        return

    game = Game(board)

    start = lines.index("Commands:") + 1

    for line in lines[start:]:

        if not line:
            continue

        command = CommandParser.parse(line)

        if isinstance(command, ClickCommand):
            game.click(
                command.x,
                command.y
            )

        elif isinstance(command, WaitCommand):
            game.wait(
                command.ms
            )

        elif isinstance(command, JumpCommand):
            game.jump(
                command.x,
                command.y
            )

        elif isinstance(command, PrintBoardCommand):
            BoardPrinter.print(
                game.get_board()
            )


if __name__ == "__main__":
    main()
