from model.board import Board
from model.piece import Piece
from model.position import Position
from realtime.move import Move

from bus.events import GameOverEvent, GameStartedEvent
from engine.game_engine import GameEngine
from view.audio.sound_player import SoundPlayer
from view.hud.game_over_tracker import GameOverTracker


def test_sound_player_and_tracker_both_receive_game_over():
    pawn = Piece("w", "P")
    board = Board([
        [Piece("b", "K")],
        [pawn],
    ])
    engine = GameEngine(board)

    sound = SoundPlayer()
    tracker = GameOverTracker()
    engine.subscribe(GameStartedEvent, sound.on_game_started)
    engine.subscribe(GameOverEvent, sound.on_game_over)
    engine.subscribe(GameOverEvent, tracker.on_game_over)

    engine.start_game()
    engine._arbiter.add_move(Move(
        pawn,
        Position(1, 0),
        Position(0, 0),
        start_time=0,
        duration=100,
    ))
    engine.tick(100)

    assert ("game_started",) in sound.played
    assert any(entry[0] == "game_over" for entry in sound.played)
    assert tracker.game_over is True
    assert tracker.notification_count == 1
