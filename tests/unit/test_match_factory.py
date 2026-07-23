"""Unit tests for MatchFactory."""

from server.services.match_factory import MatchFactory


def test_factory_configure_sets_callbacks():
    calls = {}

    def on_over(match):
        calls["over"] = match

    def on_grace(match, color):
        calls["grace"] = (match, color)

    factory = MatchFactory(
        clock=object(),
        grace_ms=5000,
        on_game_over=on_over,
        on_grace_expired=on_grace,
    )
    match = factory.create("g_test")
    assert match.game_id == "g_test"
    assert match._grace_ms == 5000
    assert match._game_over_handler is on_over
    assert match._grace_expire_handler is on_grace
