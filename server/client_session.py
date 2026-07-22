import itertools
import uuid


_connection_counter = itertools.count(1)


def _next_connection_id():
    return f"conn_{next(_connection_counter)}_{uuid.uuid4().hex[:8]}"


class ClientSession:
    """
    Per-connection identity for a networked client (Stage C/E).

    Distinct from PlaySession — this is server-side connection membership,
    not the UI play port.
    """

    def __init__(self, websocket, connection_id=None):
        self.connection_id = connection_id or _next_connection_id()
        self.websocket = websocket
        self.user_id = None
        self.username = None
        self.rating = None
        self.assigned_color = None
        self.game_id = None
        self.role = None
        self.disconnected = False

    @property
    def is_authenticated(self):
        return self.user_id is not None

    @property
    def is_identified(self):
        return self.assigned_color is not None and self.username is not None

    def bind_user(self, user_id, username, rating):
        self.user_id = user_id
        self.username = username
        self.rating = rating

    def bind_player(self, username, color, game_id):
        self.username = username
        self.assigned_color = color
        self.game_id = game_id
        self.role = "player"
        self.disconnected = False

    def bind_spectator(self, username, game_id):
        self.username = username
        self.assigned_color = None
        self.game_id = game_id
        self.role = "spectator"
        self.disconnected = False

    def clear_seat(self):
        """Release match seat / spectator slot without clearing authentication."""
        self.assigned_color = None
        self.game_id = None
        self.role = None
        self.disconnected = False

    def clear_identity(self):
        """Backward-compatible alias: clear seat only (keep auth)."""
        self.clear_seat()
