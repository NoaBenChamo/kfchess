from input.commands import (
    ClickCommand,
    WaitCommand,
    PrintCommand
)

from input.jump_command import JumpCommand

from board_io.board_printer import BoardPrinter



class ScriptRunner:


    def __init__(
        self,
        controller
    ):

        self._controller = controller

    def run(self, commands):

        for command in commands:

            if isinstance(command, ClickCommand):

                self._controller.click(
                    command.x,
                    command.y
                )

            elif isinstance(command, WaitCommand):

                self._controller.wait(
                    command.ms
                )

            elif isinstance(command, PrintCommand):

                BoardPrinter.print(
                    self._controller.get_board()
                )

            elif isinstance(command, JumpCommand):

                self._controller.jump(
                    command.x,
                    command.y
                )

