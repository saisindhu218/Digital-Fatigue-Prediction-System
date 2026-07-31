"""
CongiGuard Desktop Agent - entry point.

Usage:
    python main.py pair <CODE>                 # recommended: pair using the
                                                  # code shown on the website
                                                  # (no password needed)
    python main.py login <email> <password>   # alternative: email/password
    python main.py login                       # interactive prompt
    python main.py run                          # start background tracking
    python main.py status                       # show current config/state

When packaged with PyInstaller (see build_exe.bat), this becomes
CongiGuardAgent.exe, and `run` mode is what the Startup shortcut /
Scheduled Task launches.
"""

import getpass
import sys
import threading
import time
import uuid

import requests

import auth
import config
import heartbeat
import uploader
from logger import ActivityLogger

SAMPLE_INTERVAL_SECONDS = 60          # take one activity snapshot per minute
                                       # (upload cadence is now controlled by
                                       # logger.AGGREGATE_WINDOW -- every 10
                                       # samples collapse into 1 upload)
HEARTBEAT_INTERVAL_SECONDS = 30       # "I'm alive" ping


def cmd_pair(code: str | None):
    """Pairs this laptop to an account using the 6-character code shown
    on the website's Device Pairing / first-login setup page -- reuses
    the SAME backend endpoint the QR-code flow already uses
    (/pairing/verify-pairing), so no password ever touches the agent."""

    server_url = config.get_server_url()

    if not code:
        code = input("Enter the pairing code shown on the website: ").strip()

    device_id = config.get_or_create_device_id()

    try:
        response = requests.post(
            f"{server_url}/api/v1/pairing/verify-pairing",
            params={"token": code.strip().upper(), "scanning_device_id": device_id},
            timeout=15,
        )
    except requests.RequestException as e:
        print(f"❌ Could not reach server at {server_url}: {e}")
        sys.exit(1)

    if response.status_code == 404:
        print("❌ That code is invalid. Double-check it and try again.")
        sys.exit(1)
    if response.status_code == 410:
        print("❌ That code has expired. Generate a new one on the website and retry.")
        sys.exit(1)
    if response.status_code != 200:
        print(f"❌ Pairing failed: {response.status_code} {response.text[:200]}")
        sys.exit(1)

    user_id = response.json().get("user_id")
    config.save_paired_user(user_id)
    config.set_server_url(server_url)  # remember it -- no env var needed next time
    print(f"✅ Paired successfully. This laptop is now linked to your account.")
    print(f"   Server saved: {server_url}")
    print("You can now run: python main.py run")


def cmd_login(email: str | None, password: str | None):
    server_url = config.get_server_url()
    print(f"Logging in to {server_url} ...")

    if not email:
        email = input("Email: ").strip()
    if not password:
        password = getpass.getpass("Password: ")

    try:
        user_id = auth.login(email, password)
        config.set_server_url(server_url)  # remember it -- no env var needed next time
        print(f"✅ Logged in. user_id={user_id}")
        print(f"   Server saved: {server_url}")
        print("You can now run: python main.py run")
    except auth.AuthError as e:
        print(f"❌ Login failed: {e}")
        sys.exit(1)


def cmd_status():
    cfg = config.load_config()
    print("Server URL:  ", config.get_server_url())
    print("Device ID:   ", cfg.get("device_id", "(not set yet)"))
    user_id = cfg.get("user_id")
    print("Linked to:   ", user_id if user_id else "(not paired / logged in yet)")


def _heartbeat_loop(stop_event: threading.Event):
    while not stop_event.is_set():
        heartbeat.send_heartbeat()
        stop_event.wait(HEARTBEAT_INTERVAL_SECONDS)


def cmd_run():
    if not config.get_user_id():
        print("❌ Not paired/logged in yet.")
        print("   Run: python main.py pair <CODE>   (code shown on the website)")
        print("   or:  python main.py login")
        sys.exit(1)

    print("=" * 60)
    print("CongiGuard Desktop Agent - starting background tracking")
    print("Server:", config.get_server_url())
    print("Device:", config.get_or_create_device_id())
    print("=" * 60)

    session_id = str(uuid.uuid4())
    activity_logger = ActivityLogger()

    stop_event = threading.Event()
    threading.Thread(target=_heartbeat_loop, args=(stop_event,), daemon=True).start()
    # Send one heartbeat immediately so the dashboard shows "connected"
    # right away instead of waiting a full interval.
    heartbeat.send_heartbeat()

    last_sample_time = time.time()

    try:
        while True:
            time.sleep(1)
            now = time.time()

            if now - last_sample_time >= SAMPLE_INTERVAL_SECONDS:
                activity_logger.collect_minute_sample()
                last_sample_time = now

                if activity_logger.has_full_aggregate_window():
                    aggregate = activity_logger.build_aggregate_record()
                    if aggregate:
                        if uploader.upload_aggregate(aggregate, session_id):
                            activity_logger.discard_aggregate_window()
                        else:
                            print("[UPLOAD] Failed, will retry with next window (data kept)")

    except KeyboardInterrupt:
        print("\nStopping agent...")
        stop_event.set()


def main():
    args = sys.argv[1:]

    if not args or args[0] == "run":
        cmd_run()
    elif args[0] == "pair":
        code = args[1] if len(args) > 1 else None
        cmd_pair(code)
    elif args[0] == "login":
        email = args[1] if len(args) > 1 else None
        password = args[2] if len(args) > 2 else None
        cmd_login(email, password)
    elif args[0] == "status":
        cmd_status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
