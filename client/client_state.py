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

    @property
    def ready(self):
        return self._snapshot_dict is not None and self.assigned_color is not None

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
