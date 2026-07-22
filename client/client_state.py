from client.snapshot_codec import snapshot_dict_to_game_snapshot


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
        self.disconnect_notice = None

    @property
    def ready(self):
        if self._snapshot_dict is None:
            return False
        if self.role == "spectator":
            return True
        return self.assigned_color is not None

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
            self.role = "player"
            self.disconnect_notice = None
            self.last_error = None
            return

        if message_type == "room_update":
            self.room_id = payload.get("room_id")
            self.game_id = payload.get("game_id") or self.game_id
            if payload.get("role") is not None:
                self.role = payload.get("role")
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
            assigned = self.assigned_color
            if assigned and assigned in ratings:
                self.rating = ratings[assigned].get("rating_after", self.rating)
            self.last_error = None
            return

        if message_type == "identity_assigned":
            self.username = payload.get("username")
            self.assigned_color = payload.get("color")
            self.game_id = payload.get("game_id")
            self.role = "player"
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

        if message_type == "error":
            self.last_error = payload
            self.selected = None

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

    def create_snapshot(self):
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
            )
        return snapshot_dict_to_game_snapshot(
            self._snapshot_dict,
            selected_cell=self.selected,
        )

    @property
    def snapshot_dict(self):
        return self._snapshot_dict
