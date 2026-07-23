import itertools
import uuid

from server.session_role_enum import SessionRole


_connection_counter = itertools.count(1)


def _next_connection_id():
    return f"conn_{next(_connection_counter)}_{uuid.uuid4().hex[:8]}"


class ClientSession:
    """
    ClientSession represents the state of a single WebSocket connection to the server.
    This is the identity of the connection between the server and the client.
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
    def is_in_game(self):
        return self.assigned_color is not None and self.username is not None

    def set_user(self, user_id, username, rating):
        self.user_id = user_id
        self.username = username
        self.rating = rating

    def join_as_player(self, username, color, game_id):
        self.username = username
        self.assigned_color = color
        self.game_id = game_id
        self.role = SessionRole.PLAYER
        self.disconnected = False

    def join_as_spectator(self, username, game_id):
        self.username = username
        self.assigned_color = None
        self.game_id = game_id
        self.role = SessionRole.SPECTATOR
        self.disconnected = False

    def leave_game(self):
        self.assigned_color = None
        self.game_id = None
        self.role = None
        self.disconnected = False