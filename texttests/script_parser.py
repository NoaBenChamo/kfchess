from input.command_parser import CommandParser


class ScriptParser:


    @staticmethod
    def parse(lines):

        commands = []

        reading = False


        for line in lines:

            line = line.strip()


            if line == "Commands:":
                reading = True
                continue


            if reading and line:

                command = CommandParser.parse(
                    line
                )

                if command is not None:
                    commands.append(command)


        return commands