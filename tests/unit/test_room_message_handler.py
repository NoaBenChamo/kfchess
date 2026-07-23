"""Unit tests for RoomMessageHandler broadcast."""

import pytest

from server.handlers.room_message_handler import RoomMessageHandler


@pytest.mark.asyncio
async def test_broadcast_room_update_skips_without_room_id():
    handler = RoomMessageHandler(
        {},
        registry={},
        rooms=object(),
        matchmaker=object(),
        default_game_id="default",
        create_match_fn=None,
        start_tick_if_running_fn=None,
        start_rated_fn=None,
    )

    class _Match:
        room_id = None

    await handler.broadcast_room_update(_Match())
