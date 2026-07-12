class ScriptRunner:


    def __init__(self, controller, game):

        self._controller = controller
        self._game = game



    def run(self, commands):

        output = []


        for command in commands:


            if command[0] == "click":

                self._controller.click(
                    command[1],
                    command[2]
                )


            elif command[0] == "wait":

                self._game.wait(
                    command[1]
                )


            elif command[0] == "print":

                output.append(
                    str(
                        self._game.get_board()
                    )
                )


        return output