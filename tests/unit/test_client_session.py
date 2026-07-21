from server.client_session import ClientSession
from server.match import Match
from shared.protocol import SERVER_FULL, USERNAME_TAKEN


class _FakeSocket:
    pass


def test_client_session_starts_unidentified():
    session = ClientSession(_FakeSocket(), connection_id="c1")
    assert session.connection_id == "c1"
    assert not session.is_identified
    assert session.username is None
    assert session.assigned_color is None


def test_client_session_bind_player_sets_identity():
    session = ClientSession(_FakeSocket())
    session.bind_player("Noa", "w", "default")

    assert session.is_identified
    assert session.username == "Noa"
    assert session.assigned_color == "w"
    assert session.game_id == "default"
    assert session.role == "player"


def test_first_assign_is_white_second_is_black():
    match = Match("default")
    first = ClientSession(_FakeSocket())
    second = ClientSession(_FakeSocket())

    result_a = match.try_assign_player(first, "Alice")
    result_b = match.try_assign_player(second, "Bob")

    assert result_a == {"ok": True, "color": "w"}
    assert result_b == {"ok": True, "color": "b"}
    assert first.assigned_color == "w"
    assert second.assigned_color == "b"
    assert match.player_count() == 2
    assert match.session_for(first.websocket) is first
    assert match.session_for(second.websocket) is second


def test_third_assign_returns_server_full():
    match = Match("default")
    match.try_assign_player(ClientSession(_FakeSocket()), "Alice")
    match.try_assign_player(ClientSession(_FakeSocket()), "Bob")

    third = ClientSession(_FakeSocket())
    result = match.try_assign_player(third, "Carol")

    assert result["ok"] is False
    assert result["error_code"] == SERVER_FULL
    assert not third.is_identified
    assert match.player_count() == 2


def test_duplicate_username_is_rejected():
    match = Match("default")
    match.try_assign_player(ClientSession(_FakeSocket()), "Alice")

    second = ClientSession(_FakeSocket())
    result = match.try_assign_player(second, "alice")

    assert result["ok"] is False
    assert result["error_code"] == USERNAME_TAKEN
    assert match.player_count() == 1


def test_release_frees_seat_for_next_player():
    match = Match("default")
    first = ClientSession(_FakeSocket())
    second = ClientSession(_FakeSocket())
    match.try_assign_player(first, "Alice")
    match.try_assign_player(second, "Bob")

    released = match.release(first.websocket)

    assert released is first
    assert not first.is_identified
    assert match.player_count() == 1
    assert match.session_for(first.websocket) is None
    assert first.websocket not in match._connections

    third = ClientSession(_FakeSocket())
    result = match.try_assign_player(third, "Carol")
    assert result == {"ok": True, "color": "w"}


def test_release_unknown_websocket_is_safe():
    match = Match("default")
    assert match.release(_FakeSocket()) is None
