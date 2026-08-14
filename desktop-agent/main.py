"""
CongiGuard Desktop Agent - entry point.

Usage:
    Double-click the .exe (or run with no arguments) -- if not yet
    paired, it will interactively ask for the pairing code shown on the
    website, then start tracking automatically. If already paired, it
    just starts tracking straight away.

    python main.py pair <CODE>                 # pair non-interactively
    python main.py login <email> <password>   # alternative: email/password
    python main.py login                       # interactive login prompt
    python main.py run                          # start tracking (skips pairing check UI)
    python main.py status                       # show current config/state

When packaged with PyInstaller (see build_exe.bat), this becomes
CongiGuardAgent.exe.
"""

import getpass
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta

import requests

import auth
import config
import heartbeat
import uploader
from logger import ActivityLogger


TASK_NAME = "CongiGuardAgent"


def _get_own_exe_path() -> str | None:
    """Returns the path to THIS running program, wherever the user
    actually put it -- works no matter where the .exe was downloaded to,
    since it doesn't assume any fixed folder structure."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller-built .exe
        return sys.executable
    return None  # Running from source (python main.py) -- nothing to register


def _get_startup_folder_path() -> str:
    return os.path.join(
        os.getenv("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
    )


def _register_via_startup_folder(exe_path: str) -> bool:
    """Fallback auto-start method that needs ZERO special permissions --
    any file placed in this per-user folder runs automatically at every
    Windows login. Used when schtasks is blocked (common on
    managed/locked-down machines via Group Policy, even without needing
    real admin rights for the scheduled task itself)."""

    try:
        startup_dir = _get_startup_folder_path()
        os.makedirs(startup_dir, exist_ok=True)

        launcher_path = os.path.join(startup_dir, "CongiGuardAgent.bat")
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write(f'@echo off\r\nstart "" "{exe_path}" run\r\n')

        print(f"✅ Registered to start automatically at Windows login (Startup folder: {launcher_path})")
        return True
    except Exception as e:
        print(f"⚠️ Startup folder registration also failed: {e}")
        return False


def _remove_startup_folder_entry():
    """Deletes any leftover Startup-folder launcher from a previous run
    -- needed when switching TO the Scheduled Task method, so a stale
    entry pointing at an old/moved .exe path doesn't linger and fail at
    every login alongside the working registration."""
    try:
        launcher_path = os.path.join(_get_startup_folder_path(), "CongiGuardAgent.bat")
        if os.path.exists(launcher_path):
            os.remove(launcher_path)
    except Exception:
        pass  # best-effort cleanup, not worth failing pairing over


def _remove_scheduled_task():
    """Deletes any leftover Scheduled Task from a previous run -- needed
    when switching TO the Startup folder method, for the same reason as
    above, in reverse."""
    try:
        subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
            capture_output=True, text=True, timeout=15,
        )
    except Exception:
        pass  # best-effort cleanup


def ensure_auto_start_registered():
    """Registers this agent to start automatically at every Windows
    login, using THIS exe's actual current location. Tries a Scheduled
    Task first; if that's blocked (Access denied -- common on managed/
    locked-down machines), falls back to the classic Startup folder
    method instead, which needs no special permissions at all.

    Whichever method succeeds, the OTHER method's leftovers (from a
    previous run, possibly pointing at an old/moved .exe path) get
    cleaned up -- otherwise both can end up registered at once, and
    Windows tries to launch a stale, no-longer-existing path at every
    login alongside the correct one.

    No-op on non-Windows or when running from source."""

    if os.name != "nt":
        return

    exe_path = _get_own_exe_path()
    if not exe_path:
        return  # running from source, e.g. `python main.py` during dev

    try:
        result = subprocess.run(
            [
                "schtasks", "/Create",
                "/TN", TASK_NAME,
                "/TR", f'"{exe_path}" run',
                "/SC", "ONLOGON",
                "/RL", "LIMITED",
                "/F",
            ],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            print(f"✅ Registered to start automatically at Windows login (from {exe_path})")
            _remove_startup_folder_entry()
            return
        else:
            print(f"⚠️ Scheduled Task registration blocked: {result.stderr.strip()}")
            print("   Trying the Startup folder method instead...")
    except Exception as e:
        print(f"⚠️ Scheduled Task registration failed: {e}")
        print("   Trying the Startup folder method instead...")

    if _register_via_startup_folder(exe_path):
        _remove_scheduled_task()
    else:
        print("   You can still run 'CongiGuardAgent.exe run' manually any time.")


SAMPLE_INTERVAL_SECONDS = 60          # take one activity snapshot per minute
                                       # (upload cadence is now controlled by
                                       # logger.AGGREGATE_WINDOW -- every 10
                                       # samples collapse into 1 upload)
HEARTBEAT_INTERVAL_SECONDS = 30       # "I'm alive" ping

# If the gap between two consecutive loop ticks (which normally run every
# 1 second) is bigger than this, the laptop was almost certainly asleep
# (lid closed) rather than the app just being briefly slow. Comfortably
# above normal scheduling jitter, comfortably below "definitely asleep".
SLEEP_GAP_THRESHOLD_SECONDS = 90


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
        return False

    if response.status_code == 404:
        print("❌ That code is invalid. Double-check it and try again.")
        return False
    if response.status_code == 410:
        print("❌ That code has expired. Generate a new one on the website and retry.")
        return False
    if response.status_code != 200:
        print(f"❌ Pairing failed: {response.status_code} {response.text[:200]}")
        return False

    user_id = response.json().get("user_id")
    config.save_paired_user(user_id)
    config.set_server_url(server_url)  # remember it -- no env var needed next time
    print(f"✅ Paired successfully. This laptop is now linked to your account.")
    print(f"   Server saved: {server_url}")
    ensure_auto_start_registered()
    return True


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
        ensure_auto_start_registered()
        print("Tracking will start automatically from now on -- you can close this window.")
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


def _run_tracking_loop():
    """The actual tracking loop -- assumes pairing has already been
    confirmed by the caller."""

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
    last_tick_time = time.time()

    try:
        while True:
            time.sleep(1)
            now = time.time()

            # ---- Sleep/resume detection ----
            # If way more real time passed than the 1-second sleep()
            # call accounts for, the laptop was suspended (lid closed)
            # for that gap, not just briefly slow.
            tick_gap = now - last_tick_time
            if tick_gap > SLEEP_GAP_THRESHOLD_SECONDS:
                gap_seconds = tick_gap
                sleep_start = datetime.now() - timedelta(seconds=gap_seconds)
                sleep_end = datetime.now()

                print(f"[SLEEP] Detected laptop was asleep for {gap_seconds/60:.1f} min")

                if not uploader.upload_break(
                    start_iso=sleep_start.isoformat(),
                    end_iso=sleep_end.isoformat(),
                    duration_minutes=round(gap_seconds / 60, 2),
                    session_id=session_id,
                ):
                    print("[SLEEP] Failed to log break (non-fatal, continuing)")

                # Don't let the sleep gap corrupt idle-time or session-
                # length math -- pretend the agent "started" this much
                # later, and reset the idle-time clock to now.
                activity_logger.session_start += timedelta(seconds=gap_seconds)
                activity_logger.last_input_time = datetime.now()
                last_sample_time = now  # skip counting the gap as a sample

                # Heartbeat immediately so the dashboard reflects "back
                # online" right away instead of waiting up to 30s.
                heartbeat.send_heartbeat()

            last_tick_time = now

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


def cmd_run():
    """Used by the Scheduled Task / Startup entry -- assumes pairing is
    already done, exits with an error message if not (no interactive
    prompt here, since there may be no one watching this window)."""
    if not config.get_user_id():
        print("❌ Not paired/logged in yet.")
        print("   Run: CongiGuardAgent.exe pair <CODE>   (code shown on the website)")
        sys.exit(1)

    _run_tracking_loop()


def cmd_default():
    """What happens on a plain double-click / no arguments. This is the
    real first-time-user experience: if not paired yet, ask for the code
    right here (no separate terminal, no command syntax to remember),
    then start tracking immediately in the same window. If already
    paired, just start tracking straight away."""

    if not config.get_user_id():
        print("=" * 60)
        print("Welcome to CongiGuard")
        print("=" * 60)
        print("This laptop isn't linked to an account yet.")
        print("Go to your dashboard's 'Connect this laptop' page to get a code.")
        print()

        if not cmd_pair(None):
            print("\nPairing failed. Close this window, get a fresh code, and try again.")
            input("Press Enter to exit...")
            sys.exit(1)

        print()

    _run_tracking_loop()


def main():
    args = sys.argv[1:]

    if not args:
        cmd_default()
    elif args[0] == "run":
        cmd_run()
    elif args[0] == "pair":
        code = args[1] if len(args) > 1 else None
        if cmd_pair(code):
            print("You can now run: CongiGuardAgent.exe run  (or just double-click it)")
    elif args[0] == "login":
        email = args[1] if len(args) > 1 else None
        password = args[2] if len(args) > 2 else None
        cmd_login(email, password)
    elif args[0] == "status":
        cmd_status()
    elif args[0] == "install":
        ensure_auto_start_registered()
    else:
        print(__doc__)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        # Without this, an unhandled crash anywhere in the program just
        # closes the console window instantly -- looks like the app
        # "vanished" with zero explanation. Print the real error and
        # wait for a keypress so it's actually visible before closing.
        import traceback
        print("\n" + "=" * 60)
        print("CongiGuard crashed. Full error below:")
        print("=" * 60)
        traceback.print_exc()
        print("=" * 60)
        input("\nPress Enter to close this window...")
        sys.exit(1)
