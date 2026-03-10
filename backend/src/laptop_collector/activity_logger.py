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

import time,uuid,sys,threading,schedule,requests
from datetime import datetime
from pynput import keyboard,mouse

API_BASE="http://localhost:8000"


def get_active_user():
    try:
        r=requests.get(f"{API_BASE}/api/v1/pairing/active-user",timeout=5)
        data=r.json()
        if data.get("user_id"):
            return data["user_id"]
    except:
        pass
    return "unknown_user"


class LaptopActivityLogger:

    def __init__(self,user_id,device_id):

        self.user_id=user_id
        self.device_id=device_id

        self.session_id=str(uuid.uuid4())
        self.session_start=datetime.now()

        self.keystroke_count=0
        self.mouse_click_count=0
        self.mouse_move_count=0

        self.last_input_time=datetime.now()

        self.current_app=None
        self.current_title=None
        self.last_signature=None

        self.app_switch_count=0

        self.activity_buffer=[]

        self.start_input_listeners()
        self.start_window_monitor()

    def start_input_listeners(self):

        def on_key_press(key):
            self.keystroke_count+=1
            self.last_input_time=datetime.now()

        def on_click(x,y,button,pressed):
            if pressed:
                self.mouse_click_count+=1
                self.last_input_time=datetime.now()

        def on_move(x,y):
            self.mouse_move_count+=1
            self.last_input_time=datetime.now()

        keyboard.Listener(on_press=on_key_press,daemon=True).start()
        mouse.Listener(on_click=on_click,on_move=on_move,daemon=True).start()

    def get_active_window(self):

        try:
            if sys.platform=="win32":

                import win32gui,win32process,psutil

                hwnd=win32gui.GetForegroundWindow()
                title=win32gui.GetWindowText(hwnd)

                _,pid=win32process.GetWindowThreadProcessId(hwnd)

                process=psutil.Process(pid).name()

                return process,title

        except:
            pass

        return "Unknown","Unknown"

    def start_window_monitor(self):

        def monitor():

            while True:

                try:

                    app,title=self.get_active_window()

                    signature=f"{app}|{title}"

                    if self.last_signature is None:

                        self.current_app=app
                        self.current_title=title
                        self.last_signature=signature

                    elif signature!=self.last_signature:

                        self.current_app=app
                        self.current_title=title
                        self.app_switch_count+=1
                        self.last_signature=signature

                except:
                    pass

                time.sleep(2)

        threading.Thread(target=monitor,daemon=True).start()

    def get_app_category(self,app,title):

        name=(app+" "+title).lower()

        high=["code","pycharm","intellij","studio","notepad","sublime"]
        medium=["word","excel","powerpoint","docs"]
        low=["youtube","netflix","spotify","instagram","facebook"]

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

        session_minutes=(now-self.session_start).total_seconds()/60

        hour=now.hour

        if 5<=hour<12: time_of_day="morning"
        elif 12<=hour<17: time_of_day="afternoon"
        elif 17<=hour<22: time_of_day="evening"
        else: time_of_day="night"

        app=self.current_app if self.current_app else "Unknown"
        title=self.current_title if self.current_title else ""

        category=self.get_app_category(app,title)

        data={
            "user_id":self.user_id,
            "device_id":self.device_id,
            "session_id":self.session_id,
            "timestamp":now.isoformat(),
            "app_name":app,
            "window_title":title,
            "app_category":category,
            "usage_duration":1,
            "session_length_minutes":session_minutes,
            "idle_time_seconds":idle_seconds,
            "keystrokes":self.keystroke_count,
            "mouse_clicks":self.mouse_click_count,
            "mouse_moves":self.mouse_move_count,
            "app_switches":self.app_switch_count,
            "time_of_day":time_of_day
        }

        self.activity_buffer.append(data)

        print(f"[COLLECTED] {app} | Keys:{self.keystroke_count} | Clicks:{self.mouse_click_count} | Switches:{self.app_switch_count} | Idle:{int(idle_seconds)}s")

        self.keystroke_count=0
        self.mouse_click_count=0
        self.mouse_move_count=0
        self.app_switch_count=0

        if len(self.activity_buffer)>=5:

            self.send_to_server()

    def send_to_server(self):

        if not self.activity_buffer:
            return

        try:

            r=requests.post(
                f"{API_BASE}/api/v1/usage/laptop/batch",
                json={"records":self.activity_buffer},
                timeout=10
            )

            if r.status_code==200:

                print(f"[SYNC] Sent {len(self.activity_buffer)} records")

                self.activity_buffer.clear()

        except Exception as e:

            print("[NETWORK ERROR]",e)

    def start(self):

        print("\nStarting Laptop Activity Logger")
        print("User:",self.user_id)
        print("Device:",self.device_id)

        schedule.every(1).minutes.do(self.collect_activity)
        schedule.every(5).minutes.do(self.send_to_server)

        def loop():
            while True:
                schedule.run_pending()
                time.sleep(1)

        threading.Thread(target=loop,daemon=True).start()

        while True:
            time.sleep(1)


def main():

    user=get_active_user()
    device="laptop_"+uuid.uuid4().hex[:6]
    logger=LaptopActivityLogger(user,device)
    logger.start()


if __name__=="__main__":
    main()