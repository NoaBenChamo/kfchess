from enum import Enum


class SessionRole(str, Enum):
    PLAYER = "player"
    SPECTATOR = "spectator"
