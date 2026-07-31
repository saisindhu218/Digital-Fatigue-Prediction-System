"""
Authentication for the desktop agent.

Reuses your EXISTING /api/v1/auth/login and /api/v1/auth/refresh
endpoints -- no new backend auth logic needed. The agent behaves like
just another client of your API.
"""

import requests

import config


class AuthError(Exception):
    pass


def login(email: str, password: str) -> str:
    """Logs in, stores tokens locally, returns user_id."""

    server_url = config.get_server_url()

    try:
        response = requests.post(
            f"{server_url}/api/v1/auth/login",
            json={"email": email, "password": password},
            timeout=15,
        )
    except requests.RequestException as e:
        raise AuthError(f"Could not reach server at {server_url}: {e}")

    if response.status_code != 200:
        detail = response.json().get("detail", "Login failed") if response.content else "Login failed"
        raise AuthError(detail)

    data = response.json()
    config.save_tokens(data["access_token"], data.get("refresh_token", ""), data["user_id"])
    return data["user_id"]


def get_valid_access_token() -> str:
    """Returns a usable access token, refreshing it if needed."""

    access_token, refresh_token, user_id = config.get_tokens()

    if not access_token:
        raise AuthError("Not logged in. Run 'python main.py login' first.")

    if _token_is_valid(access_token):
        return access_token

    if not refresh_token:
        raise AuthError("Session expired and no refresh token stored. Please log in again.")

    server_url = config.get_server_url()

    try:
        response = requests.post(
            f"{server_url}/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=15,
        )
    except requests.RequestException as e:
        raise AuthError(f"Could not reach server to refresh session: {e}")

    if response.status_code != 200:
        raise AuthError("Session expired. Please log in again.")

    data = response.json()
    config.save_tokens(data["access_token"], data.get("refresh_token", refresh_token), user_id)
    return data["access_token"]


def _token_is_valid(token: str) -> bool:
    """Best-effort check: decode the JWT payload (no verification needed,
    the server is the source of truth) and check expiry with a small
    safety margin."""

    import base64
    import json
    import time

    try:
        payload_b64 = token.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        exp = payload.get("exp")
        if exp is None:
            return True
        return time.time() < (exp - 60)  # refresh 60s before real expiry
    except Exception:
        return False
