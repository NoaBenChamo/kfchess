# KFChess

Python implementation of the Kung Fu Chess project.

---

# Project Structure

```text
kfchess/

model/
    position.py
    piece.py
    board.py
    game_state.py

rules/
    piece_rules/
        movement_rule.py
        pawn_rule.py
        knight_rule.py
        bishop_rule.py
        rook_rule.py
        queen_rule.py
        king_rule.py
    rule_engine.py
    rule_factory.py
    capture_rule.py
    game_over_rule.py
    path_checker.py
    promotion_rule.py

realtime/
    move.py
    jump.py
    clock.py
    movement_time.py
    movement_validator.py
    crossing_detector.py
    real_time_arbiter.py

engine/
    game_engine.py

input/
    board_mapper.py
    controller.py
    commands.py
    command_parser.py

board_io/
    board_parser.py
    board_printer.py
    board_validator.py

config/
    constants.py

view/
    piece_state.py
    piece_snapshot.py
    game_snapshot.py
    renderer.py
    input_handler.py
    game_runner.py
    game_view/
        game_view.py
        game_layout.py
        board_view.py
        player_view.py
        header_view.py

texttests/
    script_parser.py
    script_runner.py

tests/
    unit/
    integration/

assets/
    board.png
    pieces/

app.py       ← text-based entry point (script mode)
main.py      ← graphical entry point (OpenCV window)
```

---

# Architecture

The project follows a layered architecture.

Each layer has a single responsibility and communicates only through its public interface.

The main design goals are:

* Single Responsibility Principle (SRP)
* Separation of Concerns
* Modular architecture
* Low coupling
* High cohesion
* Easy unit testing
* Easy future extension

---

# Layer Responsibilities

## Model

Responsible only for representing the logical game state.

Contains:

* `Position` — a board cell identified by row and column
* `Piece` — a chess piece with color, type, state (PieceState), and rest timer
* `Board` — an 8×8 grid of pieces with get/set/is_inside operations
* `GameState` — board + selected position + game_over flag (used in legacy flows)

The Model layer does **not** contain:

* movement rules
* game logic
* timing
* rendering
* input handling
* script parsing

---

## Rules

Responsible only for validating chess movement rules.

Contains:

* `RuleEngine` — delegates move validation to the correct piece rule
* `RuleFactory` — maps piece type (K/Q/R/B/N/P) to its rule object
* `piece_rules/` — one rule class per piece type (MovementRule base, then PawnRule, KnightRule, BishopRule, RookRule, QueenRule, KingRule)
* `PathChecker` — checks whether a path between two cells is clear (static and dynamic, accounting for active moves)
* `CaptureRule` — determines whether one piece can capture another (color check)
* `GameOverRule` — detects whether a captured piece is a king
* `PromotionRule` — detects whether a pawn has reached the promotion row and promotes it to a queen

The Rules layer never modifies the board and has no knowledge of timing or rendering.

---

## Realtime

Responsible only for real-time behavior.

Contains:

* `Move` — represents a piece travelling from source to target over a duration; provides pixel interpolation and path traversal
* `Jump` — represents a piece lifted into the air for a fixed duration with a parabolic y-offset; can capture an enemy that arrives during the jump
* `GameClock` — a simple millisecond counter advanced by `tick(ms)`
* `MovementTime` — calculates move duration from distance and per-piece speed (configured in `constants.py`)
* `MovementValidator` — checks whether a position is currently occupied by an active move
* `CrossingDetector` — detects and resolves collisions between two friendly pieces moving toward the same cell; shortens or cancels the losing move
* `RealTimeArbiter` — owns the clock, active moves, active jumps, and game events; resolves arrivals, captures, friendly blocking, jump landings, rest states, and pawn promotion

The Realtime layer never validates chess movement rules.

---

## Engine

Contains:

* `GameEngine` — the central coordinator

Responsibilities:

* receive `select`, `move_request`, `jump`, and `tick` calls
* delegate move validation to `RuleEngine`
* delegate time management and arrival resolution to `RealTimeArbiter`
* build a `GameSnapshot` for the view on every frame
* detect and propagate game-over

GameEngine never contains piece-specific movement logic.

---

## Input

Contains:

* `BoardMapper` — an injected, per-window mapper that converts pixel coordinates to `Position` and back using `BoardRect`
* `Controller` — translates click/jump/tick calls into `GameEngine` requests; handles selection, re-selection of a friendly piece, and move requests
* `Command` / `ClickCommand` / `WaitCommand` / `PrintCommand` / `JumpCommand` — plain data objects representing script commands
* `CommandParser` — parses a single text line into the appropriate Command object

The Input layer never modifies the board directly.

---

## board_io

Contains:

* `BoardParser` — reads lines in `Board: … Commands:` format and builds a `Board` with `Piece` objects
* `BoardPrinter` — prints a board to stdout in the same token format
* `BoardValidator` — validates that every token in a cell list is a known piece or empty marker

No game logic exists in this layer.

---

## Config

Contains:

* `constants.py` — all shared constants: `VALID_COLORS`, `VALID_PIECES`, `PIECE_SPEED`, `PAWN_START_ROW`, `PAWN_PROMOTION_ROW`, `JUMP_DURATION`, `SHORT_REST_DURATION`, `LONG_REST_DURATION`

---

## View

Contains:

* `PieceState` — enum: `IDLE`, `MOVE`, `JUMP`, `SHORT_REST`, `LONG_REST`
* `PieceSnapshot` — immutable data object describing one piece for the renderer (color, type, position, state, optional pixel coords, optional rest progress)
* `GameSnapshot` — immutable data object describing the full frame (board dimensions, list of PieceSnapshots, selected cell, game_over flag)
* `Renderer` — receives a `GameSnapshot`, delegates entirely to `GameView.render` and `GameView.present`
* `InputHandler` — listens to keyboard (`q` to quit) and mouse events (left-click → Controller.click, right-click → Controller.jump)
* `GameRunner` — owns the main loop: calls `engine.tick`, `engine.create_snapshot`, `renderer.render`, and `input_handler.handle` every 16 ms

### game_view/

The `game_view` sub-package coordinates the complete screen layout:

```
┌────────────────────────────────────────────┐
│                  HEADER                    │
├──────────────┬──────────────┬──────────────┤
│ LEFT PLAYER  │    BOARD     │ RIGHT PLAYER │
└──────────────┴──────────────┴──────────────┘
```

* `GameLayout` — calculates the pixel geometry (position and size) of every screen region (header, left panel, board, right panel) from the board dimensions
* `GameView` — owns the full-screen canvas; coordinates `HeaderView`, left `PlayerView`, `BoardView`, and right `PlayerView`; composites all sub-views into the canvas each frame
* `AssetsManager` — loads and caches the board image and resized piece-sprite frames
* `BoardView` — all board rendering: draws the managed assets, performs pixel interpolation for semantic move/jump progress, selection highlight, cooldown/rest progress bars, coordinate labels (A–H / 1–8), and game-over text
* `HeaderView` — top area; currently renders a plain dark bar; reserved for future game title or status information
* `PlayerView` — side panel for one player; currently renders a plain dark bar; reserved for future player name, captured pieces, and move history — **player data and move history are not yet implemented**

Rendering never modifies the game state.

---

## Text Tests

Contains:

* `ScriptParser` — reads lines after `Commands:` and returns a list of Command objects
* `ScriptRunner` — executes a list of commands against a `Controller` (click, wait, print, jump)

The script runner interacts with the game only through the public API.

---

## Tests

```text
tests/
    unit/
        test_model.py
        test_board_parser.py
        test_board_printer.py
        test_piece_rules.py
        test_rule_engine.py
        test_rules.py
        test_realtime.py
        test_real_time_arbiter.py
        test_crossing_detector.py
        test_move_path.py
        test_path_checker_dynamic.py
        test_find_last_free_cell.py
        test_game_engine.py
        test_controller.py
    integration/
        test_game_flow.py
```

---

# Entry Points

| File | Description |
|------|-------------|
| `main.py` | Graphical mode — opens an OpenCV window and runs the real-time game loop |
| `app.py` | Text/script mode — reads a board + command script from stdin and executes it |

---

# Dependency Flow

```text
Text Tests / UI
        │
        ▼
    GameRunner
        │
        ▼
    Controller
        │
        ▼
   GameEngine
    /       \
   ▼         ▼
RuleEngine  RealTimeArbiter
     \      /
      ▼    ▼
       Model
```

Within the View layer:

```text
GameRunner
    │
    ▼
 Renderer
    │
    ▼
 GameView
  /  |  \
 ▼   ▼   ▼
HeaderView  PlayerView(×2)  BoardView
```

Each layer may depend only on lower layers.

---

# Design Rules

* Every class has one responsibility.
* Keep classes small and focused.
* Avoid duplicated logic.
* Prefer composition over unnecessary complexity.
* Keep the architecture modular.
* Do not bypass the GameEngine.
* RuleEngine validates moves but never changes the board.
* RealTimeArbiter manages time but never validates chess rules.
* Controller translates input but never executes game logic.
* Renderer only displays data.
* Board represents data only and does not manage the game.

---

# Testing Strategy

Unit tests verify each layer independently.

Integration tests verify the complete game flow through the public API.

The architecture is designed so that every layer can be tested without depending on higher layers.

---

# Architecture Rule

**Before adding a new feature, first determine which layer owns the responsibility. If a class starts accumulating unrelated responsibilities, refactor it instead of extending it.**
