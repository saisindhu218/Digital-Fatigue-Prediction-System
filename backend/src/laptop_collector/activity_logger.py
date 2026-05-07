"""
Laptop Activity Logger - Real Time Tracking
Collects local activity signals and sends 10-minute aggregates to the backend.
"""

import os
import json
import schedule
import threading
import time
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path

import psutil
import requests
from pynput import keyboard, mouse

import win32gui
import win32process


API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
LOGGER_DIR = Path(__file__).resolve().parent
ACTIVE_USER_FILE = Path(__file__).resolve().parents[2] / "active_user.txt"
DEVICE_FILE = LOGGER_DIR / "device_id.txt"
MINUTE_BUFFER_FILE = LOGGER_DIR / "minute_activity_buffer.json"
SAMPLE_INTERVAL_MINUTES = 1
AGGREGATE_SEND_INTERVAL_MINUTES = 10


def get_active_user():
    try:
        data = ACTIVE_USER_FILE.read_text(encoding="utf-8").strip()
        if "|" in data:
            return data.split("|", 1)[1].strip() or None
        return data or None
    except Exception:
        print("❌ No active user found")
        return None


class LaptopActivityLogger:
    def __init__(self, user_id, device_id):
        self.user_id = user_id
        self.device_id = device_id
        self.session_id = str(uuid.uuid4())
        self.session_start = datetime.now()

        self.keystroke_count = 0
        self.mouse_click_count = 0
        self.mouse_move_count = 0
        self.last_input_time = datetime.now()

        self.current_app = "Unknown"
        self.current_title = ""
        self.last_signature = None
        self.app_switch_count = 0
        self.time_of_day = None
        self.minute_buffer_file = MINUTE_BUFFER_FILE
        self.minute_records = self.load_minute_records()

        self.start_input_listeners()
        self.start_window_monitor()

    def refresh_user(self):
        # Keep user_id fresh in case logger started before login.
        latest_user = get_active_user()
        if latest_user:
            self.user_id = latest_user

    def load_minute_records(self):
        if not self.minute_buffer_file.exists():
            return []

        try:
            with open(self.minute_buffer_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def save_minute_records(self):
        try:
            with open(self.minute_buffer_file, "w", encoding="utf-8") as f:
                json.dump(self.minute_records, f)
        except Exception as e:
            print("[BUFFER ERROR] Failed saving minute buffer:", e)

    def start_input_listeners(self):
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

    def start_window_monitor(self):
        def monitor():
            while True:
                try:
                    app, title = self.get_active_window()
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

    def get_active_window(self):
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

    def get_app_category(self, app, title):
        name = f"{app} {title}".lower()
        high = ["code", "pycharm", "intellij", "studio", "notepad", "sublime"]
        medium = ["word", "excel", "powerpoint", "docs"]
        low = ["youtube", "netflix", "spotify", "instagram", "facebook"]

        if any(x in name for x in high):
            return "HIGH"
        if any(x in name for x in medium):
            return "MEDIUM"
        if any(x in name for x in low):
            return "LOW"
        return "MEDIUM"

    def get_idle_time(self):
        return (datetime.now() - self.last_input_time).total_seconds()

    def collect_activity(self):
        now = datetime.now()
        idle_seconds = self.get_idle_time()
        hour = now.hour
        active_app = self.current_app or "Unknown"
        active_title = self.current_title or ""
        app_category = self.get_app_category(active_app, active_title)

        if 5 <= hour < 12:
            self.time_of_day = "morning"
        elif 12 <= hour < 17:
            self.time_of_day = "afternoon"
        elif 17 <= hour < 22:
            self.time_of_day = "evening"
        else:
            self.time_of_day = "night"

        minute_record = {
            "timestamp": now.isoformat(),
            "active_app": active_app,
            "app_category": app_category,
            "idle_time_seconds": idle_seconds,
            "keystrokes": self.keystroke_count,
            "mouse_clicks": self.mouse_click_count,
            "mouse_moves": self.mouse_move_count,
            "app_switches": self.app_switch_count,
            "time_of_day": self.time_of_day,
        }
        self.minute_records.append(minute_record)
        self.save_minute_records()

        self.keystroke_count = 0
        self.mouse_click_count = 0
        self.mouse_move_count = 0
        self.app_switch_count = 0

    def send_to_server(self):
        if len(self.minute_records) < AGGREGATE_SEND_INTERVAL_MINUTES:
            return

        self.refresh_user()

        while len(self.minute_records) >= AGGREGATE_SEND_INTERVAL_MINUTES:
            chunk = self.minute_records[:AGGREGATE_SEND_INTERVAL_MINUTES]
            latest = chunk[-1]

            app_counter = Counter(r.get("active_app", "Unknown") for r in chunk)
            category_counter = Counter(r.get("app_category", "MEDIUM") for r in chunk)
            aggregate_timestamp = latest.get("timestamp") or datetime.now().isoformat()

            payload = {
                "user_id": self.user_id,
                "device_id": self.device_id,
                "session_id": self.session_id,
                "timestamp": aggregate_timestamp,
                "active_app": app_counter.most_common(1)[0][0] if app_counter else "Unknown",
                "app_category": category_counter.most_common(1)[0][0] if category_counter else "MEDIUM",
                "usage_duration": AGGREGATE_SEND_INTERVAL_MINUTES,
                "session_length_minutes": (datetime.now() - self.session_start).total_seconds() / 60,
                "idle_time_seconds": sum(float(r.get("idle_time_seconds", 0)) for r in chunk),
                "keystrokes": sum(int(r.get("keystrokes", 0)) for r in chunk),
                "mouse_clicks": sum(int(r.get("mouse_clicks", 0)) for r in chunk),
                "mouse_moves": sum(int(r.get("mouse_moves", 0)) for r in chunk),
                "app_switches": sum(int(r.get("app_switches", 0)) for r in chunk),
                "time_of_day": latest.get("time_of_day"),
            }

            try:
                response = requests.post(
                    f"{API_BASE}/api/v1/usage/laptop/batch",
                    json={"records": [payload]},
                    timeout=10,
                )

                if response.status_code == 200:
                    print(f"[SYNC] Sent 10-min aggregate from local buffer ({AGGREGATE_SEND_INTERVAL_MINUTES} samples)")
                    self.minute_records = self.minute_records[AGGREGATE_SEND_INTERVAL_MINUTES:]
                    self.save_minute_records()
                else:
                    print(f"[NETWORK ERROR] Status {response.status_code} while sending activity")
                    break
            except Exception as e:
                print("[NETWORK ERROR]", e)
                break

    def start(self):
        print("\nStarting Laptop Activity Logger")
        print("User:", self.user_id)
        print("Device:", self.device_id)
        print(f"Sampling every {SAMPLE_INTERVAL_MINUTES} minute(s), sending every {AGGREGATE_SEND_INTERVAL_MINUTES} minute(s)")

        schedule.every(SAMPLE_INTERVAL_MINUTES).minutes.do(self.collect_activity)
        schedule.every(AGGREGATE_SEND_INTERVAL_MINUTES).minutes.do(self.send_to_server)

        def loop():
            while True:
                schedule.run_pending()
                time.sleep(1)

        threading.Thread(target=loop, daemon=True).start()

        while True:
            time.sleep(1)


def main():
    user = get_active_user()

    try:
        device = DEVICE_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        device = f"laptop_{uuid.uuid4().hex[:6]}"
        DEVICE_FILE.write_text(device, encoding="utf-8")

    try:
        import socket

        hostname = socket.gethostname()
        device_name = hostname or "User Laptop"
        requests.post(
            f"{API_BASE}/api/v1/pairing/generate-qr",
            json={
                "device_id": device,
                "device_type": "laptop",
                "device_name": device_name,
                "user_id": user,
            },
            timeout=5,
        )
    except Exception:
        pass

    logger = LaptopActivityLogger(user, device)
    logger.start()


if __name__ == "__main__":
    main()
