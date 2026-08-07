"""
Uploads one aggregated 10-minute activity record to the backend.
"""

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
        print(f"[UPLOAD] Network error: {e}")
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


def upload_break(start_iso: str, end_iso: str, duration_minutes: float, session_id: str) -> bool:
    """Sends a detected sleep/lid-closed gap to the backend as a break
    record -- kept completely separate from regular activity uploads
    (different data_type on the backend) so it never gets counted as
    screen time or fed into fatigue/productivity analysis, only shown
    as its own "Breaks" stat."""

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

    try:
        response = requests.post(
            f"{server_url}/api/v1/usage/break",
            json=payload,
            timeout=15,
        )
    except requests.RequestException as e:
        print(f"[BREAK] Network error: {e}")
        return False

    if response.status_code == 200:
        print(f"[BREAK] Logged {duration_minutes:.1f} min break")
        return True

    print(f"[BREAK] Server rejected: {response.status_code} {response.text[:200]}")
    return False
