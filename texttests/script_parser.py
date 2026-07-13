from input.command_parser import CommandParser


class ScriptParser:


    # מפרסר את שורות הקלט ומחזיר רשימת פקודות להרצה
    @staticmethod
    def parse(lines):

        commands = []
        reading = False

        for line in lines:

            line = line.strip()

            # זיהוי תחילת בלוק הפקודות
            if line == "Commands:":
                reading = True
                continue

            # פירוש כל שורה לפקודה
            if reading and line:
                command = CommandParser.parse(line)
                if command is not None:
                    commands.append(command)

        return commands