"""Unit tests for GameResultService."""

import pytest

from server.services.game_result_service import GameResultService


class _Match:
    def __init__(self):
        self._recorded = False
        self.db_game_id = None
        self.disconnect_forfeit = False
        self.room_id = None
        self.game_id = "g1"
        self.rated = False
        self.cleared = False
        self.broadcasts = []

    def is_result_recorded(self):
        return self._recorded

    def mark_result_recorded(self):
        self._recorded = True

    def detect_winner_color(self):
        return "w"

    async def broadcast_message(self, message_type, payload):
        self.broadcasts.append((message_type, payload))

    def leave_all_players(self):
        self.cleared = True

    def player_for_color(self, color):
        return None


class _Rooms:
    def __init__(self):
        self.finished = []

    def mark_finished(self, game_id):
        self.finished.append(game_id)


class _Rating:
    def finalize_game(self, *args, **kwargs):
        raise AssertionError("should not finalize unrated twice")


@pytest.mark.asyncio
async def test_finalize_records_result_once():
    match = _Match()
    rooms = _Rooms()
    service = GameResultService(_Rating(), rooms)

    await service.finalize_game_over(match)
    await service.finalize_game_over(match)

    assert match.is_result_recorded()
    assert len(match.broadcasts) == 1
    assert match.broadcasts[0][0] == "game_over"
    assert match.cleared is True
