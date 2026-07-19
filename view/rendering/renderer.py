class Renderer:

    def __init__(self, game_view):
        self._game_view = game_view

    def render(self, snapshot):
        self._game_view.render(snapshot)
        self._game_view.present()
