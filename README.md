# \# KFChess

# 

# Python implementation of the Kung Fu Chess project.

# 

# \---

# 

# \# Project Structure

# 

# ```text

# kungfu\_chess/

# 

# model/

# &#x20;   position.py

# &#x20;   piece.py

# &#x20;   board.py

# &#x20;   game\_state.py

# 

# rules/

# &#x20;   piece\_rules.py

# &#x20;   rule\_engine.py

# 

# realtime/

# &#x20;   motion.py

# &#x20;   real\_time\_arbiter.py

# 

# engine/

# &#x20;   game\_engine.py

# 

# input/

# &#x20;   board\_mapper.py

# &#x20;   controller.py

# 

# io/

# &#x20;   board\_parser.py

# &#x20;   board\_printer.py

# 

# view/

# &#x20;   renderer.py

# &#x20;   image\_view.py

# 

# texttests/

# &#x20;   script\_parser.py

# &#x20;   script\_runner.py

# 

# app.py

# ```

# 

# \---

# 

# \# Architecture

# 

# The project follows a layered architecture.

# 

# Each layer has a single responsibility and communicates only through its public interface.

# 

# The main design goals are:

# 

# \* Single Responsibility Principle (SRP)

# \* Separation of Concerns

# \* Modular architecture

# \* Low coupling

# \* High cohesion

# \* Easy unit testing

# \* Easy future extension

# 

# \---

# 

# \# Layer Responsibilities

# 

# \## Model

# 

# Responsible only for representing the logical game state.

# 

# Contains:

# 

# \* Position

# \* Piece

# \* Board

# \* GameState

# 

# The Model layer does \*\*not\*\* contain:

# 

# \* movement rules

# \* game logic

# \* timing

# \* rendering

# \* input handling

# \* script parsing

# 

# \---

# 

# \## Rules

# 

# Responsible only for validating chess movement rules.

# 

# Contains:

# 

# \* PieceRules

# \* RuleEngine

# 

# Responsibilities:

# 

# \* validate requested moves

# \* determine legal destinations

# \* inspect the board state

# 

# The Rules layer never modifies the board and has no knowledge of timing or rendering.

# 

# \---

# 

# \## Realtime

# 

# Responsible only for real-time behavior.

# 

# Contains:

# 

# \* Motion

# \* RealTimeArbiter

# 

# Responsibilities:

# 

# \* active motions

# \* simulated time

# \* motion completion

# \* captures

# \* collision handling

# 

# The Realtime layer never validates chess movement rules.

# 

# \---

# 

# \## Engine

# 

# Contains:

# 

# \* GameEngine

# 

# Responsibilities:

# 

# \* coordinate the game

# \* receive game requests

# \* delegate move validation

# \* delegate time management

# \* update the game state

# \* detect game over

# 

# GameEngine should never contain piece-specific movement logic.

# 

# \---

# 

# \## Input

# 

# Contains:

# 

# \* BoardMapper

# \* Controller

# 

# Responsibilities:

# 

# \* convert screen coordinates into board positions

# \* translate user actions into game requests

# 

# The Input layer never modifies the board directly.

# 

# \---

# 

# \## IO

# 

# Contains:

# 

# \* BoardParser

# \* BoardPrinter

# 

# Responsibilities:

# 

# \* parse textual board definitions

# \* print the logical board

# 

# No game logic should exist in this layer.

# 

# \---

# 

# \## View

# 

# Contains:

# 

# \* Renderer

# \* ImageView

# 

# Responsible only for drawing the current game state.

# 

# Rendering must never modify the game state.

# 

# \---

# 

# \## Text Tests

# 

# Contains:

# 

# \* ScriptParser

# \* ScriptRunner

# 

# Responsible for executing text-based integration scripts.

# 

# The script runner must interact with the game only through the public API.

# 

# \---

# 

# \# Dependency Flow

# 

# ```text

# Text Tests / UI

# &#x20;       │

# &#x20;       ▼

# &#x20;    Controller

# &#x20;       │

# &#x20;       ▼

# &#x20;   GameEngine

# &#x20;    /       \\

# &#x20;   ▼         ▼

# RuleEngine  RealTimeArbiter

# &#x20;     \\      /

# &#x20;      ▼    ▼

# &#x20;       Model

# ```

# 

# Each layer may depend only on lower layers.

# 

# \---

# 

# \# Design Rules

# 

# \* Every class has one responsibility.

# \* Keep classes small and focused.

# \* Avoid duplicated logic.

# \* Prefer composition over unnecessary complexity.

# \* Keep the architecture modular.

# \* Do not bypass the GameEngine.

# \* RuleEngine validates moves but never changes the board.

# \* RealTimeArbiter manages time but never validates chess rules.

# \* Controller translates input but never executes game logic.

# \* Renderer only displays data.

# \* Board represents data only and does not manage the game.

# 

# \---

# 

# \# Testing Strategy

# 

# Unit tests verify each layer independently.

# 

# Integration tests verify the complete game flow through the public API.

# 

# The architecture is designed so that every layer can be tested without depending on higher layers.

# 

# \---

# 

# \# Architecture Rule

# 

# \*\*Before adding a new feature, first determine which layer owns the responsibility. If a class starts accumulating unrelated responsibilities, refactor it instead of extending it.\*\*



