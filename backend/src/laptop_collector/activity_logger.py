"""
Laptop Activity Logger - Real Time Tracking
Tracks:
- Screen time
- Idle time
- Keystrokes
- Mouse clicks
- Mouse movement
- Active application
- App category
- App switches
- Time of day
"""

import time, uuid, sys, threading, schedule, requests, json, os
from datetime import datetime
from pynput import keyboard, mouse
import win32gui
import win32process
import psutil

API_BASE = "http://localhost:8000"

def get_active_user():
    try:
        with open("../../active_user.txt", "r") as f:
            data = f.read().strip()

            # format: name|user_id
            if "|" in data:
                return data.split("|")[1]   # ✅ RETURN UUID

    except Exception:
        pass

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
        self.current_app = None
        self.current_title = None
        self.last_signature = None
        self.app_switch_count = 0
        self.time_of_day = None
        self.buffer_file = "unsent_usage.json"
        self.buffered_records = []
        self.load_buffered_records()
        self.start_input_listeners()
        self.start_window_monitor()

        # Aggregation variables for 10-minute window
        self.total_keystrokes = 0
        self.total_clicks = 0
        self.total_moves = 0
        self.total_switches = 0
        self.total_idle = 0
        self.sample_count = 0


        self.start_input_listeners()
        self.start_window_monitor()

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

    def load_buffered_records(self):
        self.buffered_records = []
        if os.path.exists(self.buffer_file):
            try:
                with open(self.buffer_file, "r") as f:
                    self.buffered_records = json.load(f)
            except Exception as e:
                print("[BUFFER LOAD ERROR]", e)

    def save_buffered_records(self):
        try:
            with open(self.buffer_file, "w") as f:
                json.dump(self.buffered_records, f)
        except Exception as e:
            print("[BUFFER SAVE ERROR]", e)

    def start_window_monitor(self):
        def monitor():
            while True:
                try:
                    app, title = self.get_active_window()
                    signature = f"{app}|{title}"
                    if self.last_signature is None:
                        self.current_app = app
                        self.current_title = title
                        self.last_signature = signature
                    elif signature != self.last_signature:
                        self.current_app = app
                        self.current_title = title
                        self.app_switch_count += 1
                        self.last_signature = signature
                except Exception:
                    pass
                time.sleep(2)
        threading.Thread(target=monitor, daemon=True).start()

    def get_active_window(self):
        """
        Returns (app_name, window_title) for the current active window on Windows.
        Requires pywin32: pip install pywin32
        """
        try:
            import win32gui
            import win32process
            import psutil
        except ImportError:
            return "Unknown", "pywin32 not installed"

        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            app_name = proc.name()
            # Optionally, prettify Chrome/Edge/Firefox window titles
            if app_name.lower() in ["chrome.exe", "msedge.exe", "firefox.exe"]:
                if " - " in window_title:
                    window_title = window_title.rsplit(" - ", 1)[0]
            return app_name, window_title
        except Exception as e:
            return "Unknown", str(e)

    def get_app_category(self, app, title):
        name = (app + " " + title).lower()
        high = ["code", "pycharm", "intellij", "studio", "notepad", "sublime"]
        medium = ["word", "excel", "powerpoint", "docs"]
        low = ["youtube", "netflix", "spotify", "instagram", "facebook"]
        if any(x in name for x in high):
            return "HIGH"
        elif any(x in name for x in medium):
            return "MEDIUM"
        elif any(x in name for x in low):
            return "LOW"
        return "MEDIUM"

    def get_idle_time(self):
        return (datetime.now() - self.last_input_time).total_seconds()

    def collect_activity(self):
        now = datetime.now()
        idle_seconds = self.get_idle_time()
        session_minutes = (now - self.session_start).total_seconds() / 60
        hour = now.hour
        if 5 <= hour < 12:
            self.time_of_day = "morning"
        elif 12 <= hour < 17:
            self.time_of_day = "afternoon"
        elif 17 <= hour < 22:
            self.time_of_day = "evening"
        else:
            self.time_of_day = "night"
        app = self.current_app if self.current_app else "Unknown"
        title = self.current_title if self.current_title else ""
        category = self.get_app_category(app, title)
        record = {
            "user_id": self.user_id,
            "device_id": self.device_id,
            "session_id": self.session_id,
            "timestamp": now.isoformat(),
            "active_app": app,
            "app_category": category,
            "usage_duration": 1,
            "session_length_minutes": session_minutes,
            "idle_time_seconds": idle_seconds,
            "keystrokes": self.keystroke_count,
            "mouse_clicks": self.mouse_click_count,
            "mouse_moves": self.mouse_move_count,
            "app_switches": self.app_switch_count,
            "time_of_day": self.time_of_day
        }
        self.buffered_records.append(record)
        self.save_buffered_records()
        self.keystroke_count = 0
        self.mouse_click_count = 0
        self.mouse_move_count = 0
        self.app_switch_count = 0

    def send_to_server(self):
        if not self.buffered_records:
            return
        try:
            r = requests.post(
                f"{API_BASE}/api/v1/usage/laptop/batch",
                json={"records": self.buffered_records},
                timeout=10
            )
            if r.status_code == 200:
                print(f"[SYNC] Sent {len(self.buffered_records)} records to server.")
                self.buffered_records = []
                self.save_buffered_records()
            else:
                print(f"[NETWORK ERROR] Status {r.status_code}, buffered {len(self.buffered_records)} record(s)")
        except Exception as e:
            print("[NETWORK ERROR]", e, f"Buffered {len(self.buffered_records)} record(s)")

    def start(self):
        print("\nStarting Laptop Activity Logger")
        print("User:", self.user_id)
        print("Device:", self.device_id)
        schedule.every(1).minutes.do(self.collect_activity)
        schedule.every(10).minutes.do(self.send_to_server)
        def loop():
            while True:
                schedule.run_pending()
                time.sleep(1)
        threading.Thread(target=loop, daemon=True).start()
        while True:
            time.sleep(1)


    # Duplicate methods and unused code removed. All logic is implemented above.

        if any(x in name for x in high):
            return "HIGH"
        elif any(x in name for x in medium):
            return "MEDIUM"
        elif any(x in name for x in low):
            return "LOW"
        return "MEDIUM"

    def get_idle_time(self):
        return (datetime.now()-self.last_input_time).total_seconds()

    def collect_activity(self):

        now=datetime.now()

        idle_seconds=self.get_idle_time()

        # session_minutes removed (was unused)

        hour=now.hour

        if 5<=hour<12:
            self.time_of_day="morning"
        elif 12<=hour<17:
            self.time_of_day="afternoon"
        elif 17<=hour<22:
            self.time_of_day="evening"
        else:
            self.time_of_day="night"
        
        # app and title removed (were unused)

        # category removed (was unused)

        # ---- aggregation instead of storing every minute ----

        self.total_keystrokes+=self.keystroke_count
        self.total_clicks+=self.mouse_click_count
        self.total_moves+=self.mouse_move_count
        self.total_switches+=self.app_switch_count
        self.total_idle+=idle_seconds

        self.sample_count+=1

        # silent collection (no per-minute logs)

        # reset minute counters
        self.keystroke_count=0
        self.mouse_click_count=0
        self.mouse_move_count=0
        self.app_switch_count=0


    def send_to_server(self):

        if self.sample_count==0:
            return

        now=datetime.now()

        data={
            "user_id":self.user_id,
            "device_id":self.device_id,
            "session_id":self.session_id,
            "timestamp":now.isoformat(),
            "active_app":self.current_app if self.current_app else "Unknown",
            "app_category":self.get_app_category(self.current_app or "",self.current_title or ""),
            "usage_duration":10,
            "session_length_minutes":(now-self.session_start).total_seconds()/60,
            "idle_time_seconds":self.total_idle,
            "keystrokes":self.total_keystrokes,
            "mouse_clicks":self.total_clicks,
            "mouse_moves":self.total_moves,
            "app_switches":self.total_switches,
            "time_of_day": self.time_of_day
        }

        try:

            r=requests.post(
                f"{API_BASE}/api/v1/usage/laptop/batch",
                json={"records":[data]},
                timeout=10
            )

            if r.status_code==200:

                print(f"[SYNC] 10-min record sent | Samples: {self.sample_count}")

                self.total_keystrokes=0
                self.total_clicks=0
                self.total_moves=0
                self.total_switches=0
                self.total_idle=0
                self.sample_count=0

        except Exception as e:

            print("[NETWORK ERROR]",e)


    def start(self):

        print("\nStarting Laptop Activity Logger")
        print("User:",self.user_id)
        print("Device:",self.device_id)

        # collect usage every 1 minute
        schedule.every(1).minutes.do(self.collect_activity)

        # send aggregated record every 10 minutes
        schedule.every(10).minutes.do(self.send_to_server)

        def loop():
            while True:
                schedule.run_pending()
                time.sleep(1)

        threading.Thread(target=loop,daemon=True).start()

        while True:
            time.sleep(1)


def main():

    user = get_active_user()

    # ---------------- LOAD OR CREATE DEVICE ID ----------------

    device_file = "device_id.txt"

    try:

        with open(device_file, "r") as f:
            device = f.read().strip()

    except Exception:
        device = "laptop_" + uuid.uuid4().hex[:6]
        with open(device_file, "w") as f:
            f.write(device)

    # ---------------- REGISTER DEVICE IN BACKEND ----------------

    import socket
    hostname = socket.gethostname()
    device_name = hostname or "User Laptop"


    try:
        requests.post(
            f"{API_BASE}/api/v1/pairing/generate-qr",
            json={
                "device_id": device,
                "device_type": "laptop",
                "device_name": device_name,
                "user_id": user
            },
            timeout=5
        )
    except Exception:
        pass

    # ---------------- START LOGGER ----------------

    logger = LaptopActivityLogger(user, device)
    logger.start()

if __name__=="__main__":
    main()