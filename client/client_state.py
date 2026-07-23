from client.snapshot_codec import snapshot_dict_to_game_snapshot
from server.session_role_enum import SessionRole
        

class ClientState:
    """
    Holds the latest authoritative snapshot from the server plus local UI selection.
    """

    def __init__(self):
        self._snapshot_dict = None
        self.selected = None
        self.sequence = -1
        self.last_error = None
        self.user_id = None
        self.username = None
        self.rating = None
        self.assigned_color = None
        self.game_id = None
        self.room_id = None
        self.role = None
        self.players = {}
        self.opponent_username = None
        self.opponent_rating = None
        self.matchmaking_waiting = False
        self.disconnect_notice = None

    @property
    def ready(self):
        if self._snapshot_dict is None:
            return False
        # Explicitly stay on the waiting screen while queued for matchmaking.
        if self.matchmaking_waiting:
            return False
        if self.role == SessionRole.SPECTATOR:
            return True
        if self.assigned_color is None:
            return False
        # Private room: wait until both seats are filled before opening the board.
        if self.room_id is not None:
            return "w" in self.players and "b" in self.players
        return True

    @property
    def game_over(self):
        if self._snapshot_dict is None:
            return False
        return bool(self._snapshot_dict.get("game_over"))

    def handle_message(self, message):
        message_type = message.get("type")
        payload = message.get("payload") or {}

        if message_type == "auth_ok":
            self.user_id = payload.get("user_id")
            self.username = payload.get("username")
            self.rating = payload.get("rating")
            self.last_error = None
            return

        if message_type == "match_found":
            self.assigned_color = payload.get("color")
            self.game_id = payload.get("game_id")
            self.role = SessionRole.PLAYER
            self.matchmaking_waiting = False
            opponent = payload.get("opponent") or {}
            self.opponent_username = opponent.get("username") or self.opponent_username
            if "rating" in opponent:
                self.opponent_rating = opponent.get("rating")
            self.disconnect_notice = None
            self.last_error = None
            return

        if message_type == "request_ok":
            status = payload.get("status")
            if status == "waiting":
                self.matchmaking_waiting = True
            elif status in ("cancelled", "not_waiting"):
                self.matchmaking_waiting = False
            return

        if message_type == "matchmaking_timeout":
            self.matchmaking_waiting = False
            self.last_error = {
                "code": "MATCHMAKING_TIMEOUT",
                "message": "No suitable opponent found. Please try again.",
            }
            return

        if message_type == "room_update":
            self.room_id = payload.get("room_id")
            self.game_id = payload.get("game_id") or self.game_id
            if "players" in payload:
                self.players = payload.get("players") or {}
            if payload.get("role") is not None:
                self.role = SessionRole(payload.get("role"))
            if payload.get("color") is not None:
                self.assigned_color = payload.get("color")
            self.last_error = None
            return

        if message_type == "player_disconnected":
            self.disconnect_notice = {
                "color": payload.get("color"),
                "grace_period_ms": payload.get("grace_period_ms"),
            }
            return

        if message_type == "player_reconnected":
            self.disconnect_notice = None
            return

        if message_type == "game_over":
            ratings = payload.get("ratings") or {}
            self._apply_game_over_ratings(ratings)
            self.last_error = None
            return

        if message_type == "identity_assigned":
            self.username = payload.get("username")
            self.assigned_color = payload.get("color")
            self.game_id = payload.get("game_id")
            self.role = SessionRole.PLAYER
            self.last_error = None
            return

        if message_type == "state_snapshot":
            self._apply_snapshot(payload)
            return

        if message_type == "move_accepted":
            snapshot = payload.get("snapshot")
            if snapshot is not None:
                self._apply_snapshot(snapshot)
            self.selected = None
            self.last_error = None
            return

        if message_type == "jump_accepted":
            snapshot = payload.get("snapshot")
            if snapshot is not None:
                self._apply_snapshot(snapshot)
            self.last_error = None
            return

        if message_type == "error":
            self.last_error = payload
            self.selected = None

    def _apply_game_over_ratings(self, ratings):
        """Update own and opponent ratings from game_over payload."""
        for color, info in ratings.items():
            after = info.get("rating_after")
            if after is None:
                continue
            if color in self.players:
                seated = dict(self.players[color])
                seated["rating"] = after
                self.players[color] = seated
            if color == self.assigned_color:
                self.rating = after
            elif self.assigned_color is not None:
                opponent_color = "b" if self.assigned_color == "w" else "w"
                if color == opponent_color:
                    self.opponent_rating = after

    def _apply_snapshot(self, payload):
        sequence = payload.get("sequence", 0)
        if self._snapshot_dict is not None and sequence < self.sequence:
            return
        self.sequence = sequence
        self._snapshot_dict = payload

    def clear_selection(self):
        self.selected = None

    def select(self, position):
        self.selected = position

    def player_usernames(self):
        """Resolve white/black display names from room seats or matchmaking."""
        white = None
        black = None
        if self.players:
            white_info = self.players.get("w") or {}
            black_info = self.players.get("b") or {}
            white = white_info.get("username")
            black = black_info.get("username")

        if self.role == SessionRole.SPECTATOR:
            return white, black

        if self.assigned_color == "w":
            white = white or self.username
            black = black or self.opponent_username
        elif self.assigned_color == "b":
            black = black or self.username
            white = white or self.opponent_username
        return white, black

    def player_ratings(self):
        """Resolve white/black ELO from room seats or matchmaking identity."""
        white = None
        black = None
        if self.players:
            white_info = self.players.get("w") or {}
            black_info = self.players.get("b") or {}
            white = white_info.get("rating")
            black = black_info.get("rating")

        if self.role == SessionRole.SPECTATOR:
            return white, black

        if self.assigned_color == "w":
            white = white if white is not None else self.rating
            black = black if black is not None else self.opponent_rating
        elif self.assigned_color == "b":
            black = black if black is not None else self.rating
            white = white if white is not None else self.opponent_rating
        return white, black

    def hud_line(self):
        """Short status line for the game header."""
        parts = []
        if self.room_id:
            parts.append(f"Private Room {self.room_id}")
        else:
            parts.append("Matchmaking")
        if self.role == SessionRole.SPECTATOR:
            parts.append("Spectator — read only")
        if self.disconnect_notice is not None:
            color = self.disconnect_notice.get("color")
            label = "White" if color == "w" else "Black" if color == "b" else "Opponent"
            grace = self.disconnect_notice.get("grace_period_ms")
            if grace is not None:
                parts.append(f"{label} disconnected — {int(grace) // 1000}s to reconnect")
            else:
                parts.append(f"{label} disconnected")
        return " · ".join(parts)

    def create_snapshot(self):
        white_name, black_name = self.player_usernames()
        white_rating, black_rating = self.player_ratings()
        if self._snapshot_dict is None:
            return snapshot_dict_to_game_snapshot(
                {
                    "board_width": 8,
                    "board_height": 8,
                    "pieces": [],
                    "game_over": False,
                    "white_moves": [],
                    "black_moves": [],
                    "white_score": 0,
                    "black_score": 0,
                    "sequence": 0,
                },
                selected_cell=self.selected,
                white_username=white_name,
                black_username=black_name,
                white_rating=white_rating,
                black_rating=black_rating,
                hud_line=self.hud_line(),
            )
        return snapshot_dict_to_game_snapshot(
            self._snapshot_dict,
            selected_cell=self.selected,
            white_username=white_name,
            black_username=black_name,
            white_rating=white_rating,
            black_rating=black_rating,
            hud_line=self.hud_line(),
        )

    @property
    def snapshot_dict(self):
        return self._snapshot_dict
