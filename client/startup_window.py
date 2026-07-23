"""Single OpenCV window for login, lobby, and waiting before the game."""

import asyncio
from dataclasses import dataclass

import cv2
import numpy as np

from client.network_client import NetworkClient
from client.remote_session import (
    MODE_CREATE_ROOM,
    MODE_JOIN_ROOM,
    MODE_MATCHMAKING,
    RemoteSession,
)
from server.session_role_enum import SessionRole

WINDOW_NAME = "KFChess"
WIDTH = 640
HEIGHT = 480
BG = (40, 40, 40)
BUTTON = (80, 120, 80)
BUTTON_HOVER = (100, 150, 100)
FIELD = (30, 30, 30)
FIELD_FOCUS = (50, 50, 70)
TEXT = (230, 230, 230)
ERROR = (80, 80, 220)
FONT = cv2.FONT_HERSHEY_SIMPLEX

PHASE_AUTH = "auth"
PHASE_AUTHING = "authing"
PHASE_LOBBY = "lobby"
PHASE_WAITING = "waiting"


@dataclass
class StartupResult:
    session: RemoteSession


class _Rect:
    __slots__ = ("x", "y", "w", "h", "label", "action")

    def __init__(self, x, y, w, h, label="", action=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.label = label
        self.action = action

    def contains(self, px, py):
        return self.x <= px < self.x + self.w and self.y <= py < self.y + self.h


class StartupWindow:
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._phase = PHASE_AUTH
        self._username = ""
        self._password = ""
        self._auth_mode = "login"
        self._room_id = ""
        self._status = ""
        self._error = ""
        self._session = None
        self._play_mode = None
        self._focus_field = "username"
        self._mouse_pos = (0, 0)
        self._running = True
        self._result = None
        self._pending_auth_mode = None

    # --- Public state-transition API (testable without OpenCV) ---

    @property
    def phase(self):
        return self._phase

    @property
    def status(self):
        return self._status

    @property
    def error(self):
        return self._error

    @property
    def result(self):
        return self._result

    def handle_login(self):
        """Start login authentication (same as clicking Login)."""
        self._begin_auth("login")

    def handle_register(self):
        """Start registration (same as clicking Register)."""
        self._begin_auth("register")

    def handle_key(self, key):
        """Apply a keyboard event to the current phase."""
        if self._phase in (PHASE_WAITING, PHASE_AUTHING):
            if self._phase == PHASE_WAITING and key in (ord("c"), ord("C")):
                self._cancel_waiting()
            return

        # Normalize common special keys across OpenCV backends.
        if key in (9,):
            fields = self._active_fields()
            if fields:
                try:
                    index = fields.index(self._focus_field)
                except ValueError:
                    index = 0
                self._focus_field = fields[(index + 1) % len(fields)]
            return
        if key in (8, 65288, 65535):  # Backspace variants
            self._edit_focused(backspace=True)
            return
        if key in (13, 10):  # Enter
            if self._phase == PHASE_AUTH:
                self.handle_login()
            return

        code = key & 0xFF
        if key >= 0x100000:
            return
        if 32 <= code <= 126:
            self._edit_focused(chr(code))

    def handle_click(self, x, y):
        """Apply a left-click at (x, y) — hit targets or field focus."""
        self._mouse_pos = (x, y)
        if self._phase == PHASE_AUTHING:
            return
        for rect in self._hit_targets():
            if rect.contains(x, y) and rect.action is not None:
                rect.action()
                return
        fields = self._active_fields()
        for index, rect in enumerate(self._field_rects()):
            if rect.contains(x, y) and index < len(fields):
                self._focus_field = fields[index]
                self._refocus_window()
                return

    def tick(self):
        """
        Advance non-drawing phase work (auth / waiting).

        Call from the OpenCV loop or from headless tests after handle_*.
        """
        if self._phase == PHASE_AUTHING:
            self._tick_auth()
        elif self._phase == PHASE_WAITING:
            self._tick_waiting()

    def run(self):
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, WIDTH, HEIGHT)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)

        try:
            while self._running:
                self.tick()
                frame = self._draw()
                cv2.imshow(WINDOW_NAME, frame)
                for key in self._poll_keys():
                    if key in (27,):  # Esc
                        self._running = False
                        break
                    self.handle_key(key)
                if not self._running:
                    break
        finally:
            cv2.destroyWindow(WINDOW_NAME)

        if self._session is not None and self._result is None:
            self._session.stop()
        return self._result

    def _poll_keys(self):
        """Drain OpenCV's key queue so consecutive keystrokes are not dropped."""
        keys = []
        key = cv2.waitKeyEx(30)
        while key != -1:
            keys.append(key)
            key = cv2.waitKeyEx(1)
        return keys

    def _tick_waiting(self):
        if self._session is None:
            return
        self._session.pump(0)
        if self._session.ready:
            self._result = StartupResult(session=self._session)
            self._running = False
            return
        err = self._session.error
        if err is not None:
            if err.get("code") == "MATCHMAKING_TIMEOUT":
                self._error = "No suitable opponent found. Please try again."
            else:
                self._error = f"{err.get('code', 'ERROR')}: {err.get('message', '')}"
            self._session.stop()
            self._session = None
            self._phase = PHASE_LOBBY
            self._status = ""
            return
        self._update_waiting_status()

    def _update_waiting_status(self):
        if self._session is None:
            return
        state = self._session.state
        if self._play_mode == MODE_MATCHMAKING:
            self._status = "Searching for opponent (±100 ELO, up to 60s)..."
        elif self._play_mode == MODE_CREATE_ROOM:
            room = state.room_id or "..."
            self._status = f"Waiting for opponent...  Room {room}"
        elif self._play_mode == MODE_JOIN_ROOM:
            if state.role == SessionRole.SPECTATOR:
                self._status = "Room is full — joining as spectator"
            else:
                room = self._room_id or state.room_id or "..."
                self._status = f"Joining room {room}..."
        else:
            self._status = "Connecting..."

    def _start_play(self, play_mode):
        self._error = ""
        if play_mode == MODE_JOIN_ROOM and not self._room_id.strip():
            self._error = "Room ID is required"
            return
        uri = f"ws://{self._host}:{self._port}"
        room_id = self._room_id.strip().upper() if play_mode == MODE_JOIN_ROOM else None
        self._play_mode = play_mode
        self._session = RemoteSession(
            uri,
            username=self._username,
            password=self._password,
            auth_mode=self._auth_mode,
            play_mode=play_mode,
            room_id=room_id,
        )
        self._session.start_async()
        self._phase = PHASE_WAITING
        self._update_waiting_status()

    def _cancel_waiting(self):
        if self._session is not None:
            self._session.cancel()
            self._session = None
        self._phase = PHASE_LOBBY
        self._status = ""
        self._error = ""

    def _begin_auth(self, auth_mode):
        if not self._username.strip():
            self._error = "Username is required"
            return
        if not self._password:
            self._error = "Password is required"
            return
        self._pending_auth_mode = auth_mode
        self._error = ""
        self._status = "Authenticating..."
        self._phase = PHASE_AUTHING

    def _go_lobby(self, auth_mode):
        """Backward-compatible alias used by older unit tests."""
        self._begin_auth(auth_mode)

    def _tick_auth(self):
        auth_mode = self._pending_auth_mode or "login"
        response = self._authenticate(auth_mode)
        if response.get("type") == "auth_ok":
            # Account now exists — later RemoteSession connections must login,
            # not register again (would hit USERNAME_TAKEN).
            self._auth_mode = "login"
            self._phase = PHASE_LOBBY
            self._status = ""
            self._error = ""
            self._focus_field = "room_id"
            return

        payload = response.get("payload") or {}
        code = payload.get("code", "ERROR")
        message = payload.get("message", "authentication failed")
        self._error = f"{code}: {message}"
        self._status = ""
        self._phase = PHASE_AUTH
        self._focus_field = "username"

    def _authenticate(self, auth_mode):
        uri = f"ws://{self._host}:{self._port}"

        async def _run():
            async with NetworkClient(uri) as client:
                if auth_mode == "register":
                    return await client.register(self._username, self._password)
                return await client.login(self._username, self._password)

        # Run on a dedicated thread so OpenCV (and sync callers) stay free of
        # nested-loop issues; the UI already blocks in PHASE_AUTHING.
        def _run_in_fresh_loop():
            return asyncio.run(_run())

        try:
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(_run_in_fresh_loop).result(timeout=15)
        except Exception as exc:
            return {
                "type": "error",
                "payload": {
                    "code": "CONNECTION_ERROR",
                    "message": str(exc),
                },
            }

    def _active_fields(self):
        if self._phase == PHASE_AUTH:
            return ["username", "password"]
        if self._phase == PHASE_LOBBY:
            return ["room_id"]
        return []

    def _edit_focused(self, char=None, backspace=False):
        fields = self._active_fields()
        if not fields:
            return
        name = self._focus_field if self._focus_field in fields else fields[0]
        self._focus_field = name
        if name == "username":
            target = "_username"
        elif name == "password":
            target = "_password"
        else:
            target = "_room_id"
        value = getattr(self, target)
        if backspace:
            setattr(self, target, value[:-1])
        elif char is not None:
            setattr(self, target, value + char)

    def _on_mouse(self, event, x, y, _flags, _param):
        self._mouse_pos = (x, y)
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        self.handle_click(x, y)

    def _refocus_window(self):
        """Ensure the OpenCV window keeps receiving keystrokes after a click."""
        try:
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_TOPMOST, 1)
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_TOPMOST, 0)
        except cv2.error:
            pass

    def _field_rects(self):
        if self._phase == PHASE_AUTH:
            return [
                _Rect(120, 120, 400, 36),
                _Rect(120, 180, 400, 36),
            ]
        if self._phase == PHASE_LOBBY:
            return [_Rect(120, 280, 400, 36)]
        return []

    def _hit_targets(self):
        rects = []
        if self._phase == PHASE_AUTH:
            rects.extend([
                _Rect(120, 250, 180, 40, "Login", self.handle_login),
                _Rect(340, 250, 180, 40, "Register", self.handle_register),
            ])
        elif self._phase == PHASE_LOBBY:
            rects.extend([
                _Rect(120, 120, 400, 44, "Matchmaking", lambda: self._start_play(MODE_MATCHMAKING)),
                _Rect(120, 175, 400, 44, "Create Room", lambda: self._start_play(MODE_CREATE_ROOM)),
                _Rect(120, 230, 400, 44, "Join Room", lambda: self._start_play(MODE_JOIN_ROOM)),
                _Rect(120, 340, 120, 36, "Back", self._back_to_auth),
            ])
        elif self._phase == PHASE_WAITING:
            rects.append(
                _Rect(260, 300, 120, 40, "Cancel", self._cancel_waiting),
            )
        return rects

    def _back_to_auth(self):
        self._phase = PHASE_AUTH
        self._error = ""
        self._status = ""
        self._focus_field = "username"

    # --- Drawing only (no state transitions) ---

    def _draw(self):
        canvas = np.full((HEIGHT, WIDTH, 3), BG, dtype=np.uint8)
        cv2.putText(canvas, "KFChess", (20, 40), FONT, 1.2, TEXT, 2, cv2.LINE_AA)

        if self._phase in (PHASE_AUTH, PHASE_AUTHING):
            self._draw_label(canvas, "Username", 120, 110)
            self._draw_field(
                canvas,
                self._username,
                120,
                120,
                focused=self._focus_field == "username",
            )
            self._draw_label(canvas, "Password", 120, 170)
            masked = "*" * len(self._password)
            self._draw_field(
                canvas,
                masked,
                120,
                180,
                focused=self._focus_field == "password",
            )
            if self._phase == PHASE_AUTHING:
                cv2.putText(
                    canvas,
                    self._status or "Authenticating...",
                    (120, 320),
                    FONT,
                    0.6,
                    TEXT,
                    1,
                    cv2.LINE_AA,
                )
        elif self._phase == PHASE_LOBBY:
            mode = "Register" if self._auth_mode == "register" else "Login"
            cv2.putText(
                canvas,
                f"Logged in as {self._username} ({mode})",
                (120, 100),
                FONT,
                0.55,
                TEXT,
                1,
                cv2.LINE_AA,
            )
            self._draw_label(canvas, "Room ID (for Join)", 120, 270)
            self._draw_field(
                canvas,
                self._room_id,
                120,
                280,
                focused=self._focus_field == "room_id",
            )
        elif self._phase == PHASE_WAITING:
            cv2.putText(
                canvas,
                self._status,
                (40, 200),
                FONT,
                0.7,
                TEXT,
                1,
                cv2.LINE_AA,
            )

        if self._phase != PHASE_AUTHING:
            for rect in self._hit_targets():
                self._draw_button(canvas, rect)
        if self._error:
            cv2.putText(
                canvas, self._error, (20, HEIGHT - 20), FONT, 0.55, ERROR, 1, cv2.LINE_AA
            )
        return canvas

    def _draw_label(self, canvas, text, x, y):
        cv2.putText(canvas, text, (x, y), FONT, 0.5, TEXT, 1, cv2.LINE_AA)

    def _draw_field(self, canvas, value, x, y, focused=False):
        color = FIELD_FOCUS if focused else FIELD
        cv2.rectangle(canvas, (x, y), (x + 400, y + 36), color, -1)
        cv2.rectangle(canvas, (x, y), (x + 400, y + 36), (120, 120, 120), 1)
        cv2.putText(canvas, value, (x + 8, y + 26), FONT, 0.6, TEXT, 1, cv2.LINE_AA)

    def _draw_button(self, canvas, rect):
        hover = rect.contains(*self._mouse_pos)
        color = BUTTON_HOVER if hover else BUTTON
        cv2.rectangle(canvas, (rect.x, rect.y), (rect.x + rect.w, rect.y + rect.h), color, -1)
        cv2.rectangle(
            canvas, (rect.x, rect.y), (rect.x + rect.w, rect.y + rect.h), (160, 160, 160), 1
        )
        if rect.label:
            scale = 0.55
            size = cv2.getTextSize(rect.label, FONT, scale, 1)[0]
            tx = rect.x + (rect.w - size[0]) // 2
            ty = rect.y + (rect.h + size[1]) // 2
            cv2.putText(canvas, rect.label, (tx, ty), FONT, scale, TEXT, 1, cv2.LINE_AA)


def run_startup_window(host, port):
    """Show pre-game UI. Returns StartupResult or None if cancelled."""
    return StartupWindow(host, port).run()
