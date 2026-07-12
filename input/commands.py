class Command:
    pass


class ClickCommand(Command):

    def __init__(self, x, y):
        self.x = x
        self.y = y


class WaitCommand(Command):

    def __init__(self, ms):
        self.ms = ms


class PrintCommand(Command):
    pass