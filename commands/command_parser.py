from commands.commands import *
from jump_command import JumpCommand

class CommandParser:


    @staticmethod
    def parse(line):

        parts = line.split()

        if parts[0] == "click":

            return ClickCommand(
                int(parts[1]),
                int(parts[2])
            )


        if parts[0] == "wait":

            return WaitCommand(
                int(parts[1])
            )


        if parts[0] == "print":

            return PrintBoardCommand()
        
        if parts[0] == "jump":
            return JumpCommand(
                int(parts[1]),
                int(parts[2])
            )