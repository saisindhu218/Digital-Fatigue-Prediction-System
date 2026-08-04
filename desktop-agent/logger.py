"""
Activity Logger - collects keyboard/mouse/window activity using OS-level
hooks. Matches your ORIGINAL backend/src/laptop_collector/activity_logger.py
design exactly: raw samples are captured once per minute internally, then
collapsed into a single AGGREGATE record (dominant app, summed counts,
precise session length) every 10 samples before upload -- one Mongo write
per 10 minutes, not ten.

Windows-only (uses pywin32) for active-window detection; degrades
gracefully elsewhere.
"""

import time
from collections import Counter
from datetime import datetime

import psutil
from pynput import keyboard, mouse

try:
    import win32gui
    import win32process
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


HIGH_FOCUS_APPS = ["code", "pycharm", "intellij", "studio", "notepad", "sublime", "vim", "terminal"]
MEDIUM_FOCUS_APPS = ["word", "excel", "powerpoint", "docs", "outlook", "teams", "slack"]
LOW_FOCUS_APPS = ["youtube", "netflix", "spotify", "instagram", "facebook", "twitter", "tiktok"]

AGGREGATE_WINDOW = 10  # collapse this many 1-minute samples into one record


class ActivityLogger:
    """Tracks keystrokes, mouse activity, and the foreground window.

    Call `collect_minute_sample()` once a minute. Once at least
    AGGREGATE_WINDOW samples have accumulated, call
    `pop_aggregate_record()` to get one summarized record representing
    that whole window (and remove those samples from the internal buffer).
    """

    def __init__(self):
        self.session_start = datetime.now()
        self.minute_records = []

        self.keystroke_count = 0
        self.mouse_click_count = 0
        self.mouse_move_count = 0
        self.last_input_time = datetime.now()

        self.current_app = "Unknown"
        self.current_title = ""
        self.last_signature = None
        self.app_switch_count = 0

        self._start_input_listeners()
        self._start_window_monitor()

    # ---------------- INPUT HOOKS ----------------

    def _start_input_listeners(self):
        def on_key_press(key):
            self.keystroke_count += 1
            self.last_input_time = datetime.now()

        def on_click(x, y, button, pressed):
            if pressed:
                self.mouse_click_count += 1
                self.last_input_time = datetime.now()

        def on_move(x, y):
            self.mouse_move_count += 1
            self.last_input_time = datetime.now()

        keyboard.Listener(on_press=on_key_press, daemon=True).start()
        mouse.Listener(on_click=on_click, on_move=on_move, daemon=True).start()

    def _start_window_monitor(self):
        import threading

        def monitor():
            while True:
                try:
                    app, title = self._get_active_window()
                    signature = f"{app}|{title}"
                    if signature != self.last_signature:
                        self.current_app = app
                        self.current_title = title
                        if self.last_signature is not None:
                            self.app_switch_count += 1
                        self.last_signature = signature
                except Exception:
                    pass
                time.sleep(2)

        threading.Thread(target=monitor, daemon=True).start()

    def _get_active_window(self):
        if not HAS_WIN32:
            return "Unknown", "pywin32 not available"

        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            app_name = proc.name()

            if app_name.lower() in ["chrome.exe", "msedge.exe", "firefox.exe"] and " - " in window_title:
                window_title = window_title.rsplit(" - ", 1)[0]

            return app_name, window_title
        except Exception as e:
            return "Unknown", str(e)

    @staticmethod
    def get_app_category(app: str, title: str) -> str:
        name = f"{app} {title}".lower()
        if any(x in name for x in HIGH_FOCUS_APPS):
            return "HIGH"
        if any(x in name for x in MEDIUM_FOCUS_APPS):
            return "MEDIUM"
        if any(x in name for x in LOW_FOCUS_APPS):
            return "LOW"
        return "MEDIUM"

    @staticmethod
    def _time_of_day_bucket(hour: int) -> str:
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 17:
            return "afternoon"
        if 17 <= hour < 22:
            return "evening"
        return "night"

    # ---------------- SAMPLING (every 1 minute, internal only) ----------------

    def collect_minute_sample(self):
        """Snapshot the last minute of raw activity into the internal
        buffer, then reset the per-minute counters. Does NOT get uploaded
        directly -- see pop_aggregate_record()."""

        now = datetime.now()
        idle_seconds = (now - self.last_input_time).total_seconds()

        minute_record = {
            "timestamp": now.isoformat(),
            "active_app": self.current_app or "Unknown",
            "app_category": self.get_app_category(self.current_app, self.current_title),
            "idle_time_seconds": idle_seconds,
            "keystrokes": self.keystroke_count,
            "mouse_clicks": self.mouse_click_count,
            "mouse_moves": self.mouse_move_count,
            "app_switches": self.app_switch_count,
            "time_of_day": self._time_of_day_bucket(now.hour),
        }

        self.minute_records.append(minute_record)

        # reset per-minute counters
        self.keystroke_count = 0
        self.mouse_click_count = 0
        self.mouse_move_count = 0
        self.app_switch_count = 0

        return minute_record

    # ---------------- AGGREGATION (every AGGREGATE_WINDOW minutes) ----------------

    def has_full_aggregate_window(self) -> bool:
        return len(self.minute_records) >= AGGREGATE_WINDOW

    def build_aggregate_record(self):
        """Builds a summarized record from the oldest AGGREGATE_WINDOW
        minute-samples WITHOUT removing them from the buffer. Returns
        None if there isn't a full window yet. Call discard_aggregate_window()
        only after the upload actually succeeds."""

        if not self.has_full_aggregate_window():
            return None

        chunk = self.minute_records[:AGGREGATE_WINDOW]

        latest = chunk[-1]
        app_counter = Counter(r.get("active_app", "Unknown") for r in chunk)
        category_counter = Counter(r.get("app_category", "MEDIUM") for r in chunk)

        # Per-app minute breakdown WITHIN this window -- each raw sample
        # in `chunk` represents exactly 1 real minute, so counting which
        # app was active in each one gives real per-app minutes, not just
        # a single "dominant app" for the whole 10-minute block. This is
        # what lets the dashboard show a real multi-app breakdown instead
        # of whichever app happened to win the window.
        app_breakdown = dict(app_counter)

        return {
            "timestamp": latest.get("timestamp"),
            "active_app": app_counter.most_common(1)[0][0] if app_counter else "Unknown",
            "app_category": category_counter.most_common(1)[0][0] if category_counter else "MEDIUM",
            "app_breakdown": app_breakdown,
            # usage_duration is in MINUTES per the backend's convention --
            # this record represents AGGREGATE_WINDOW minutes of activity.
            "usage_duration": AGGREGATE_WINDOW,
            "session_length_minutes": (datetime.now() - self.session_start).total_seconds() / 60,
            "idle_time_seconds": sum(float(r.get("idle_time_seconds", 0)) for r in chunk),
            "keystrokes": sum(int(r.get("keystrokes", 0)) for r in chunk),
            "mouse_clicks": sum(int(r.get("mouse_clicks", 0)) for r in chunk),
            "mouse_moves": sum(int(r.get("mouse_moves", 0)) for r in chunk),
            "app_switches": sum(int(r.get("app_switches", 0)) for r in chunk),
            "time_of_day": latest.get("time_of_day"),
        }

    def discard_aggregate_window(self):
        """Removes the oldest AGGREGATE_WINDOW samples after a successful
        upload. Safe to call even if fewer than AGGREGATE_WINDOW remain."""
        self.minute_records = self.minute_records[AGGREGATE_WINDOW:]
