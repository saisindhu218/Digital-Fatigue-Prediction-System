"""
Uploads one aggregated 10-minute activity record to the backend.
"""

import time

import requests

import auth
import config


def upload_aggregate(aggregate_record: dict, session_id: str) -> bool:
    """Sends a single aggregated record to /usage/laptop/batch.

    Returns True on success (caller should discard the record), False on
    failure (caller should hold onto it and retry next cycle).
    """

    if not aggregate_record:
        return True

    server_url = config.get_server_url()
    device_id = config.get_or_create_device_id()
    user_id = config.get_user_id()

    if not user_id:
        print("[UPLOAD] Skipped, not paired/logged in yet")
        return False

    # Attach a bearer token if we have one (password-login flow). The
    # pairing-code flow has no JWT and that's fine -- the backend's
    # /usage/laptop/batch endpoint identifies the record by user_id in
    # the payload, not by the Authorization header.
    headers = {}
    try:
        headers["Authorization"] = f"Bearer {auth.get_valid_access_token()}"
    except auth.AuthError:
        pass

    payload = {
        "records": [
            {
                **aggregate_record,
                "device_id": device_id,
                "user_id": user_id,
                "session_id": session_id,
            }
        ]
    }

    try:
        response = requests.post(
            f"{server_url}/api/v1/usage/laptop/batch",
            json=payload,
            headers=headers,
            timeout=15,
        )
    except requests.RequestException as e:
        print(f"[UPLOAD] {config.describe_network_error(e)}")
        return False

    if response.status_code == 200:
        print(
            f"[UPLOAD] Sent 10-min aggregate "
            f"(app={aggregate_record.get('active_app')}, "
            f"keystrokes={aggregate_record.get('keystrokes')})"
        )
        return True

    print(f"[UPLOAD] Server rejected batch: {response.status_code} {response.text[:200]}")
    return False


def upload_break(
    start_iso: str,
    end_iso: str,
    duration_minutes: float,
    session_id: str,
    max_retries: int = 4,
    retry_delay_seconds: float = 8.0,
) -> bool:
    """Sends a detected sleep/lid-closed gap to the backend as a break
    record -- kept completely separate from regular activity uploads
    (different data_type on the backend) so it never gets counted as
    screen time or fed into fatigue/productivity analysis, only shown
    as its own "Breaks" stat.

    Unlike upload_aggregate (which naturally retries on the next
    10-minute window since the caller keeps unsent data), a break event
    is one-off -- if the first attempt fails, there's no "next window"
    to retry it on. And the very first attempt right after waking from
    sleep is exactly when it's MOST likely to fail, since WiFi typically
    takes a few seconds to reconnect after resume. So this retries a
    handful of times with a short delay before actually giving up,
    instead of a single silent failure."""

    server_url = config.get_server_url()
    device_id = config.get_or_create_device_id()
    user_id = config.get_user_id()

    if not user_id:
        print("[BREAK] Skipped, not paired/logged in yet")
        return False

    payload = {
        "device_id": device_id,
        "user_id": user_id,
        "session_id": session_id,
        "start_time": start_iso,
        "end_time": end_iso,
        "duration_minutes": duration_minutes,
    }

    last_error_summary = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                f"{server_url}/api/v1/usage/break",
                json=payload,
                timeout=15,
            )
        except requests.RequestException as e:
            last_error_summary = config.describe_network_error(e)
            if attempt < max_retries:
                time.sleep(retry_delay_seconds)
                continue
            print(f"[BREAK] {last_error_summary} (gave up after {max_retries} attempts)")
            return False

        if response.status_code == 200:
            print(f"[BREAK] Logged {duration_minutes:.1f} min break")
            return True

        print(f"[BREAK] Server rejected: {response.status_code} {response.text[:200]}")
        return False

    return False
