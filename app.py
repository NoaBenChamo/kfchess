from board_io.board_parser import BoardParser
from input.controller import Controller
from engine.game_engine import GameEngine


def main():

    lines = []

    while True:

        try:
            line = input()
            lines.append(line)

        except EOFError:
            break


    board = BoardParser.parse(lines)


    game_engine = GameEngine(
        board
    )


    controller = Controller(
        game_engine
    )


    return controller



if __name__ == "__main__":

    main()