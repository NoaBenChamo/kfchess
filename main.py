from board.board_parser import BoardParser
from board.board_validator import BoardValidator
from board.board_printer import BoardPrinter


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

    BoardPrinter.print(board)


if __name__ == "__main__":
    main()


