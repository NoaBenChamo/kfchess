from engine.game_engine import GameEngine
from model.position import Position
from snapshots.game_snapshot import GameSnapshot


class LocalSession:
    """PlaySession implementation backed by an in-process GameEngine."""

    def __init__(self, engine: GameEngine):
        self._engine = engine

    def pump(self, elapsed_ms: int) -> None:
        self._engine.tick(elapsed_ms)

    def create_snapshot(self) -> GameSnapshot:
        return self._engine.create_snapshot()

    def get_selected(self) -> Position | None:
        return self._engine.get_selected()

    def select(self, position: Position) -> None:
        self._engine.select(position)

    def clear_selection(self) -> None:
        self._engine.clear_selection()

    def request_move_to(self, target: Position) -> None:
        self._engine.move_request(target)

    def request_jump_to(self, target: Position) -> None:
        self._engine.jump(target)

    @property
    def game_over(self) -> bool:
        return self._engine.is_game_over()

    def get_board(self):
        """Local-only helper for text tests and scripting tools."""
        return self._engine.get_board()
