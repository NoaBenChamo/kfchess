"""
Automated end-to-end QA for full client–server user flows.

Uses real GameServer + NetworkClient / StartupWindow handle_* paths,
in-memory SQLite, and FakeClock (no real 60s waits, no mouse clicks).
"""

import asyncio
import time

import pytest

from client.client_state import ClientState
from client.network_client import NetworkClient
from client.remote_session import RemoteSession
from client.snapshot_codec import snapshot_dict_to_game_snapshot
from client.startup_window import PHASE_AUTH, PHASE_LOBBY, PHASE_WAITING
from engine.game_engine import GameEngine
from model.board import Board
from model.piece import Piece
from model.position import Position
from realtime.move import Move
from server.dal.repositories import UserRepository
from server.game_registry import GameRegistry
from server.match import Match
from server.session_role_enum import SessionRole
from shared.protocol import (
    INVALID_CREDENTIALS,
    ROOM_NOT_FOUND,
    SPECTATOR_READ_ONLY,
    USERNAME_TAKEN,
)
from snapshots.move_record import MoveRecord
from tests.e2e.harness import (
    FakeClock,
    MATCHMAKING_TIMEOUT_MS,
    auth_via_handlers,
    e2e_server,
    live_server,
    make_startup_window,
    matchmake_pair,
    pump_until,
    wait_for_move_in_history,
    wait_for_piece,
)
from view.hud.player_view import format_move_notation


# ---------------------------------------------------------------------------
# Auth via StartupWindow public handlers (real NetworkClient path)
# ---------------------------------------------------------------------------


def test_e2e_successful_register_and_login_via_handlers():
    with live_server() as srv:
        window = make_startup_window(srv.host, srv.port)
        for ch in "Alice":
            window.handle_key(ord(ch))
        window.handle_key(9)  # Tab → password
        for ch in "secret1":
            window.handle_key(ord(ch))

        window.handle_register()
        window.tick()
        assert window.phase == PHASE_LOBBY
        assert window.error == ""
        assert window._auth_mode == "login"

        user = srv.game_server._users.get_by_username("Alice")
        assert user is not None
        assert user.rating == 1200

        # Fresh window: login with same credentials.
        login = make_startup_window(srv.host, srv.port, "Alice", "secret1")
        login.handle_click(200, 270)  # Login button center
        login.tick()
        assert login.phase == PHASE_LOBBY
        assert login.error == ""


def test_e2e_duplicate_register_and_invalid_credentials():
    with live_server() as srv:
        first = make_startup_window(srv.host, srv.port, "Alice", "secret1")
        auth_via_handlers(first, "register")
        assert first.phase == PHASE_LOBBY

        dup = make_startup_window(srv.host, srv.port, "Alice", "other1")
        auth_via_handlers(dup, "register")
        assert dup.phase == PHASE_AUTH
        assert USERNAME_TAKEN in dup.error

        bad = make_startup_window(srv.host, srv.port, "Alice", "wrong")
        auth_via_handlers(bad, "login")
        assert bad.phase == PHASE_AUTH
        assert INVALID_CREDENTIALS in bad.error


def test_e2e_handle_key_enter_triggers_login():
    with live_server() as srv:
        # Pre-register so login succeeds.
        prep = make_startup_window(srv.host, srv.port, "Bob", "secret1")
        auth_via_handlers(prep, "register")

        window = make_startup_window(srv.host, srv.port, "Bob", "secret1")
        window.handle_key(13)  # Enter → login
        assert window.phase == "authing"
        window.tick()
        assert window.phase == PHASE_LOBBY


# ---------------------------------------------------------------------------
# Private rooms + waiting screen
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_private_room_create_join_and_waiting_until_second_player():
    async with e2e_server() as (gs, uri, port, _db):
        alice = NetworkClient(uri)
        bob = NetworkClient(uri)
        await alice.connect()
        await bob.connect()
        await alice.register("Alice", "secret1")
        await bob.register("Bob", "secret1")

        created = await alice.create_room()
        room_id = created["payload"]["room_id"]
        assert created["payload"]["color"] == "w"
        assert created["payload"]["status"] == "waiting"
        await alice.receive_until("identity_assigned")
        await alice.receive_until("match_found")
        snap = await alice.receive_until("state_snapshot")

        # Creator ClientState must stay not-ready until Black joins.
        state = ClientState()
        state.handle_message(created)
        state.handle_message({"type": "state_snapshot", "payload": snap["payload"]})
        assert state.ready is False
        assert "w" in state.players
        assert "b" not in state.players

        joined = await bob.join_room(room_id)
        assert joined["payload"]["role"] == SessionRole.PLAYER
        assert joined["payload"]["color"] == "b"
        await bob.receive_until("identity_assigned")
        await bob.receive_until("match_found")
        await bob.receive_until("state_snapshot")

        update = await alice.receive_until("room_update")
        state.handle_message(update)
        assert state.ready is True
        assert update["payload"]["players"]["b"]["username"] == "Bob"

        await alice.close()
        await bob.close()


def test_e2e_startup_creator_stays_waiting_until_joiner():
    """Drive Create Room through StartupWindow + RemoteSession (no OpenCV loop)."""
    with live_server() as srv:
        creator_ui = make_startup_window(srv.host, srv.port, "Alice", "secret1")
        auth_via_handlers(creator_ui, "register")
        creator_ui.handle_click(320, 195)  # Create Room button
        assert creator_ui.phase == PHASE_WAITING
        assert "Waiting for opponent" in creator_ui.status

        # Pump waiting ticks — must NOT become ready alone.
        for _ in range(30):
            creator_ui.tick()
            time.sleep(0.02)
            if "Room " in creator_ui.status and "..." not in creator_ui.status:
                break
        assert creator_ui.result is None
        assert creator_ui.phase == PHASE_WAITING
        room_id = creator_ui._session.state.room_id
        assert room_id

        joiner = RemoteSession(
            f"ws://{srv.host}:{srv.port}",
            username="Bob",
            password="secret1",
            auth_mode="register",
            play_mode="join_room",
            room_id=room_id,
        )
        joiner.start_async()
        assert pump_until(joiner, lambda s: s.ready, timeout=8.0)

        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            creator_ui.tick()
            if creator_ui.result is not None:
                break
            time.sleep(0.02)

        assert creator_ui.result is not None
        assert creator_ui.result.session.ready
        joiner.stop()
        creator_ui.result.session.stop()


# ---------------------------------------------------------------------------
# Matchmaking
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_matchmaking_does_not_open_board_before_opponent():
    async with e2e_server() as (_gs, uri, _port, _db):
        async with NetworkClient(uri) as client:
            await client.register("Alice", "secret1")
            waiting = await client.play_request()
            assert waiting["type"] == "request_ok"
            assert waiting["payload"]["status"] == "waiting"

            state = ClientState()
            state.handle_message(waiting)
            assert state.matchmaking_waiting is True
            assert state.ready is False


@pytest.mark.asyncio
async def test_e2e_matchmaking_only_within_elo_range():
    async with e2e_server() as (gs, uri, _port, _db):
        async with NetworkClient(uri) as a, NetworkClient(uri) as b:
            await a.register("Alice", "secret1")
            await b.register("Bob", "secret1")
            bob = gs._users.get_by_username("Bob")
            gs._users.update_rating(bob.id, 1500)
            for session in gs._sessions.values():
                if session.username == "Bob":
                    session.rating = 1500

            wait_a = await a.play_request()
            wait_b = await b.play_request()
            assert wait_a["type"] == "request_ok"
            assert wait_b["type"] == "request_ok"
            assert gs.matchmaker.queue_size == 2


@pytest.mark.asyncio
async def test_e2e_matchmaking_within_range_succeeds():
    async with e2e_server() as (_gs, uri, _port, _db):
        a, b, matched_a, matched_b, _sa, _sb = await matchmake_pair(uri)
        assert matched_a["payload"]["color"] == "w"
        assert matched_b["payload"]["color"] == "b"
        assert matched_a["payload"]["game_id"] == matched_b["payload"]["game_id"]
        await a.close()
        await b.close()


@pytest.mark.asyncio
async def test_e2e_matchmaking_timeout_after_60s_via_fake_clock():
    clock = FakeClock()
    async with e2e_server(clock=clock, start_ticks=False) as (gs, uri, _port, _db):
        async with NetworkClient(uri) as client:
            await client.register("Alice", "secret1")
            waiting = await client.play_request()
            assert waiting["type"] == "request_ok"

            clock.advance(MATCHMAKING_TIMEOUT_MS)
            await gs._expire_matchmaking()

            timeout = await client.receive_until("matchmaking_timeout")
            assert timeout["type"] == "matchmaking_timeout"
            assert gs.matchmaker.queue_size == 0

            state = ClientState()
            state.handle_message(waiting)
            state.handle_message(timeout)
            assert state.matchmaking_waiting is False
            assert state.last_error["code"] == "MATCHMAKING_TIMEOUT"


# ---------------------------------------------------------------------------
# Spectators, invalid / full room
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_spectator_joins_active_game_cannot_move():
    async with e2e_server() as (_gs, uri, _port, _db):
        async with (
            NetworkClient(uri) as white,
            NetworkClient(uri) as black,
            NetworkClient(uri) as spectator,
        ):
            await white.register("Alice", "secret1")
            await black.register("Bob", "secret1")
            await spectator.register("Carol", "secret1")

            room = await white.create_room()
            room_id = room["payload"]["room_id"]
            await white.receive_until("identity_assigned")
            await white.receive_until("match_found")
            await white.receive_until("state_snapshot")

            await black.join_room(room_id)
            await black.receive_until("identity_assigned")
            await black.receive_until("match_found")
            await black.receive_until("state_snapshot")
            await white.receive_until("room_update")

            joined = await spectator.join_room(room_id)
            assert joined["payload"]["role"] == SessionRole.SPECTATOR
            snap = await spectator.receive_until("state_snapshot")
            assert snap["type"] == "state_snapshot"

            denied = await spectator.send_move("WPe2e4")
            assert denied["type"] == "error"
            assert denied["payload"]["code"] == SPECTATOR_READ_ONLY

            jump_denied = await spectator.send_jump(6, 4)
            assert jump_denied["type"] == "error"
            assert jump_denied["payload"]["code"] == SPECTATOR_READ_ONLY


@pytest.mark.asyncio
async def test_e2e_invalid_room_code_and_full_room_as_spectator():
    async with e2e_server() as (_gs, uri, _port, _db):
        async with (
            NetworkClient(uri) as white,
            NetworkClient(uri) as black,
            NetworkClient(uri) as third,
            NetworkClient(uri) as stranger,
        ):
            await white.register("Alice", "secret1")
            await black.register("Bob", "secret1")
            await third.register("Carol", "secret1")
            await stranger.register("Dan", "secret1")

            missing = await stranger.join_room("ZZZZZZ")
            assert missing["type"] == "error"
            assert missing["payload"]["code"] == ROOM_NOT_FOUND

            room = await white.create_room()
            room_id = room["payload"]["room_id"]
            await white.receive_until("state_snapshot")
            await black.join_room(room_id)
            await black.receive_until("state_snapshot")

            # Both seats filled → third joiner is spectator ("full room").
            full = await third.join_room(room_id)
            assert full["payload"]["role"] == SessionRole.SPECTATOR
            assert full["payload"].get("color") in (None,)


# ---------------------------------------------------------------------------
# Moves: normal, capture, jump, promotion, game over + JUMP e4 history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_normal_move_jump_and_jump_e4_history():
    async with e2e_server() as (_gs, uri, _port, _db):
        a, b, *_ = await matchmake_pair(uri)
        try:
            move = await a.send_move("WPe2e4")
            assert move["type"] == "move_accepted"
            snap0 = move["payload"]["snapshot"]
            history = await wait_for_move_in_history(
                a, color="w", move_type="move", initial_payload=snap0
            )
            white_moves = history["payload"]["white_moves"]
            assert white_moves[-1]["move_type"] == "move"
            assert white_moves[-1]["target"] == {"row": 4, "col": 4}

            # Wait until pawn actually arrives on e4 before jumping.
            arrived = await wait_for_piece(
                a, row=4, col=4, color="w", piece_type="P", initial_payload=snap0
            )

            jump = await a.send_jump(4, 4)
            assert jump["type"] == "jump_accepted"
            jump_payload = jump["payload"]["snapshot"]
            jump_hist = await wait_for_move_in_history(
                a, color="w", move_type="jump", initial_payload=jump_payload
            )
            record_dict = jump_hist["payload"]["white_moves"][-1]
            assert record_dict["move_type"] == "jump"
            record = MoveRecord(
                record_dict["color"],
                record_dict["piece_type"],
                Position(record_dict["source"]["row"], record_dict["source"]["col"]),
                Position(record_dict["target"]["row"], record_dict["target"]["col"]),
                move_type="jump",
                time_ms=record_dict.get("time_ms"),
            )
            assert format_move_notation(record) == "JUMP e4"

            snap = snapshot_dict_to_game_snapshot(jump_hist["payload"])
            assert format_move_notation(snap.white_moves[-1]) == "JUMP e4"
            assert arrived["type"] == "state_snapshot"
        finally:
            await a.close()
            await b.close()


@pytest.mark.asyncio
async def test_e2e_capture_promotion_and_game_over():
    """Capture + promotion + king-capture game over on real network paths."""
    database = None
    registry = GameRegistry()

    # Board for capture: white rook takes black pawn.
    capture_board = Board([
        [Piece("w", "R"), Piece("b", "P"), None, None, None, None, None, Piece("b", "K")],
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [Piece("w", "K")] + [None] * 7,
    ])
    engine = GameEngine(capture_board)
    engine.start_game()
    match = Match("default", engine=engine)
    registry.register(match)

    async with e2e_server(registry=registry) as (gs, uri, _port, database):
        async with NetworkClient(uri) as white, NetworkClient(uri) as black:
            await white.register("Alice", "secret1")
            await black.register("Bob", "secret1")
            await white.identify("Alice")
            await white.receive_until("state_snapshot")
            await black.identify("Bob")
            await black.receive_until("state_snapshot")

            # Capture.
            cap = await white.send_move("WRa8b8")
            assert cap["type"] == "move_accepted"
            hist = await wait_for_move_in_history(white, color="w", move_type="capture")
            assert hist["payload"]["white_moves"][-1]["move_type"] == "capture"
            assert hist["payload"]["white_score"] >= 1

    # Fresh server for promotion (pawn a7→a8 empty).
    registry2 = GameRegistry()
    promo_board = Board([
        [None] + [None] * 6 + [Piece("b", "K")],
        [Piece("w", "P")] + [None] * 7,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [Piece("w", "K")] + [None] * 7,
    ])
    promo_engine = GameEngine(promo_board)
    promo_engine.start_game()
    registry2.register(Match("default", engine=promo_engine))

    async with e2e_server(registry=registry2) as (_gs2, uri2, _port2, _db2):
        async with NetworkClient(uri2) as white, NetworkClient(uri2) as black:
            await white.register("Alice", "secret1")
            await black.register("Bob", "secret1")
            await white.identify("Alice")
            await white.receive_until("state_snapshot")
            await black.identify("Bob")
            await black.receive_until("state_snapshot")

            promo = await white.send_move("WPa7a8")
            assert promo["type"] == "move_accepted"
            # Wait until pawn becomes queen on a8.
            deadline = asyncio.get_running_loop().time() + 3.0
            promoted = False
            while asyncio.get_running_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(white.receive_message(), timeout=0.4)
                except TimeoutError:
                    continue
                if msg["type"] != "state_snapshot":
                    continue
                for piece in msg["payload"]["pieces"]:
                    if (
                        piece["row"] == 0
                        and piece["col"] == 0
                        and piece["color"].lower() == "w"
                        and piece["piece_type"] == "Q"
                        and piece["state"] != "move"
                    ):
                        promoted = True
                        break
                if promoted:
                    break
            assert promoted, "pawn should promote to queen on a8"

    # Game over via king capture on rated custom match.
    registry3 = GameRegistry()
    over_board = Board([
        [Piece("b", "K")],
        [Piece("w", "P")],
    ])
    over_engine = GameEngine(over_board)
    over_engine.start_game()
    over_match = Match("default", engine=over_engine)
    registry3.register(over_match)

    async with e2e_server(registry=registry3) as (gs3, uri3, _port3, _db3):
        async with NetworkClient(uri3) as white, NetworkClient(uri3) as black:
            await white.register("Alice", "secret1")
            await black.register("Bob", "secret1")
            await white.identify("Alice")
            await white.receive_until("state_snapshot")
            await black.identify("Bob")
            await black.receive_until("state_snapshot")
            assert over_match.rated is True

            pawn = over_match.engine.get_board().get(Position(1, 0))
            now = over_match.engine._arbiter.get_time()
            async with over_match.lock:
                over_match.engine._arbiter.add_move(
                    Move(pawn, Position(1, 0), Position(0, 0), start_time=now, duration=40)
                )

            over = await white.receive_until("game_over", timeout=3.0)
            assert over["payload"]["winner"] == "w"
            assert over["payload"]["rated"] is True
            assert over["payload"]["ratings"]["w"]["rating_after"] > 1200

            users = UserRepository(gs3.database)
            assert users.get_by_username("Alice").rating > 1200
            assert users.get_by_username("Bob").rating < 1200


# ---------------------------------------------------------------------------
# Disconnect / reconnect + rating persistence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_disconnect_and_reconnect_with_fake_clock():
    clock = FakeClock()
    async with e2e_server(clock=clock, disconnect_grace_ms=60_000) as (
        gs,
        uri,
        _port,
        _db,
    ):
        white, black, *_rest = await matchmake_pair(uri)
        game_id = None
        try:
            move = await white.send_move("WPe2e4")
            assert move["type"] == "move_accepted"
            await black.receive_until("state_snapshot")

            # Find game_id from registry (non-default matchmaking games).
            matches = [m for m in gs.registry.all_matches() if m.player_count() == 2]
            assert matches
            game_id = matches[0].game_id

            await white.close()
            notice = await black.receive_until("player_disconnected")
            assert notice["payload"]["color"] == "w"
            assert notice["payload"]["grace_period_ms"] == 60_000

            restored = NetworkClient(uri)
            await restored.connect()
            auth = await restored.login("Alice", "secret1")
            assert auth["type"] == "auth_ok"
            found = await restored.receive_until("match_found")
            assert found["payload"]["game_id"] == game_id
            assert found["payload"]["color"] == "w"
            await restored.receive_until("state_snapshot")

            reconnected = await black.receive_until("player_reconnected")
            assert reconnected["payload"]["color"] == "w"

            again = await restored.send_move("WNg1f3")
            assert again["type"] == "move_accepted"

            await restored.close()
            await black.close()
        finally:
            pass


@pytest.mark.asyncio
async def test_e2e_rating_persists_across_new_connection():
    registry = GameRegistry()
    board = Board([[Piece("b", "K")], [Piece("w", "P")]])
    engine = GameEngine(board)
    engine.start_game()
    match = Match("default", engine=engine)
    registry.register(match)

    async with e2e_server(registry=registry) as (gs, uri, _port, _db):
        async with NetworkClient(uri) as white, NetworkClient(uri) as black:
            await white.register("Alice", "secret1")
            await black.register("Bob", "secret1")
            await white.identify("Alice")
            await white.receive_until("state_snapshot")
            await black.identify("Bob")
            await black.receive_until("state_snapshot")

            pawn = match.engine.get_board().get(Position(1, 0))
            now = match.engine._arbiter.get_time()
            async with match.lock:
                match.engine._arbiter.add_move(
                    Move(
                        pawn,
                        Position(1, 0),
                        Position(0, 0),
                        start_time=now,
                        duration=40,
                    )
                )
            over = await white.receive_until("game_over", timeout=3.0)
            alice_after = over["payload"]["ratings"]["w"]["rating_after"]

        async with NetworkClient(uri) as again:
            auth = await again.login("Alice", "secret1")
            assert auth["type"] == "auth_ok"
            assert auth["payload"]["rating"] == alice_after
            assert gs._users.get_by_username("Alice").rating == alice_after


# ---------------------------------------------------------------------------
# Matchmaking UI waiting status (StartupWindow)
# ---------------------------------------------------------------------------


def test_e2e_startup_matchmaking_shows_searching_not_ready():
    with live_server() as srv:
        window = make_startup_window(srv.host, srv.port, "Alice", "secret1")
        auth_via_handlers(window, "register")
        window.handle_click(320, 140)  # Matchmaking
        assert window.phase == PHASE_WAITING
        assert "Searching for opponent" in window.status
        assert "±100" in window.status
        assert "60s" in window.status

        for _ in range(20):
            window.tick()
            time.sleep(0.02)
        assert window.result is None
        assert window.phase == PHASE_WAITING

        window.handle_key(ord("c"))  # cancel
        assert window.phase == PHASE_LOBBY
