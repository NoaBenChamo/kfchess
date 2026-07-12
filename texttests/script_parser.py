class ScriptParser:


    @staticmethod
    def parse(lines):

        commands = []


        for line in lines:

            line = line.strip()


            if not line:
                continue


            parts = line.split()


            command = parts[0]


            if command == "click":

                commands.append(
                    (
                        "click",
                        int(parts[1]),
                        int(parts[2])
                    )
                )


            elif command == "wait":

                commands.append(
                    (
                        "wait",
                        int(parts[1])
                    )
                )


            elif command == "print":

                commands.append(
                    ("print",)
                )


        return commands