from input.commands import (ClickCommand,WaitCommand,PrintCommand,JumpCommand)


class CommandParser:

    # ממיר שורת טקסט ומחזיר את אובייקט הפקודה המתאים
    @staticmethod
    def parse(line):

        parts = line.split()

        if not parts:
            return None

        command = parts[0]

        # זיהוי סוג הפקודה ובניית אובייקט המתאים
        if command == "click":
            return ClickCommand(int(parts[1]), int(parts[2]))

        if command == "wait":
            return WaitCommand(int(parts[1]))

        if command == "print":
            return PrintCommand()

        if command == "jump":
            return JumpCommand(int(parts[1]), int(parts[2]))

        return None