from dataclasses import dataclass

@dataclass(frozen=True)
class GameStartedEvent:
    """Published when a playable local/network game session begins."""
    
@dataclass(frozen=True)
class GameOverEvent:
    """Published once when the game ends."""
    timestamp_ms: int
