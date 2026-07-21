import itertools
import uuid


_connection_counter = itertools.count(1)


def _next_connection_id():
    return f"conn_{next(_connection_counter)}_{uuid.uuid4().hex[:8]}"


class ClientSession:
    """
    Per-connection identity for a networked client (Stage C).

    Distinct from PlaySession — this is server-side connection membership,
    not the UI play port.
    """

    def __init__(self, websocket, connection_id=None):
        self.connection_id = connection_id or _next_connection_id()
        self.websocket = websocket
        self.username = None
        self.assigned_color = None
        self.game_id = None
        self.role = None

    @property
    def is_identified(self):
        return self.assigned_color is not None and self.username is not None

    def bind_player(self, username, color, game_id):
        self.username = username
        self.assigned_color = color
        self.game_id = game_id
        self.role = "player"

    def clear_identity(self):
        self.username = None
        self.assigned_color = None
        self.game_id = None
        self.role = None
