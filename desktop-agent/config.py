"""
Configuration for the CongiGuard Desktop Agent.

Everything the agent needs to remember between runs (server URL, JWT
tokens, device id) is stored in a small JSON file under the user's
%APPDATA% (Windows) / home folder, NOT inside the installed program
folder, so it survives updates/reinstalls and doesn't need admin rights.
"""

import json
import os
import uuid
from pathlib import Path

APP_NAME = "CongiGuard"
AGENT_VERSION = "1.0.0"

# Baked-in production backend URL. This is what makes the packaged .exe
# work out of the box for real end users -- no environment variable, no
# setup. CONGIGUARD_SERVER_URL (if set) still overrides this, which is
# how local dev/testing points the agent at localhost instead.
PRODUCTION_SERVER_URL = "https://digital-fatigue-prediction-system.onrender.com"


def _ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    _ensure_dir()

    if not CONFIG_FILE.exists():
        return {}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data: dict) -> None:
    _ensure_dir()

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_or_create_device_id() -> str:
    cfg = load_config()

    if cfg.get("device_id"):
        return cfg["device_id"]

    device_id = f"laptop_{uuid.uuid4().hex[:10]}"
    cfg["device_id"] = device_id
    save_config(cfg)
    return device_id


def get_server_url() -> str:
    """
    Priority:
      1. Value already saved in agent_config.json (set automatically the
         moment you run `pair` or `login` -- persists across terminals,
         no env var needed again)
      2. CONGIGUARD_SERVER_URL environment variable -- set this to
         override for local dev (e.g. http://localhost:8000)
      3. Baked-in production URL (PRODUCTION_SERVER_URL above) -- this is
         what a real end user's freshly downloaded .exe uses by default,
         zero setup required.
    """
    cfg = load_config()

    if cfg.get("server_url"):
        return cfg["server_url"].rstrip("/")

    env_override = os.getenv("CONGIGUARD_SERVER_URL", "").strip()
    if env_override:
        return env_override.rstrip("/")

    return PRODUCTION_SERVER_URL


def set_server_url(url: str) -> None:
    cfg = load_config()
    cfg["server_url"] = url.rstrip("/")
    save_config(cfg)


def get_tokens():
    cfg = load_config()
    return cfg.get("access_token"), cfg.get("refresh_token"), cfg.get("user_id")


def save_tokens(access_token: str, refresh_token: str, user_id: str) -> None:
    cfg = load_config()
    cfg["access_token"] = access_token
    cfg["refresh_token"] = refresh_token
    cfg["user_id"] = user_id
    save_config(cfg)


def get_user_id():
    return load_config().get("user_id")


def save_paired_user(user_id: str) -> None:
    """Used by the pairing-code flow (no password/JWT needed) -- just
    remembers which account this laptop belongs to."""
    cfg = load_config()
    cfg["user_id"] = user_id
    save_config(cfg)


def clear_tokens() -> None:
    cfg = load_config()
    for key in ("access_token", "refresh_token", "user_id"):
        cfg.pop(key, None)
    save_config(cfg)


def describe_network_error(e: Exception) -> str:
    """Turns a raw requests/urllib3 exception (often several nested lines
    of connection-pool internals) into one short, readable phrase for
    the console. Used everywhere the agent reports a failed request, so
    the terminal stays readable instead of dumping a full traceback-style
    message for routine, expected things like a laptop just having woken
    from sleep with WiFi not reconnected yet."""

    text = str(e)

    if "getaddrinfo failed" in text or "NameResolutionError" in text:
        return "no internet connection right now (DNS lookup failed)"
    if "timed out" in text.lower():
        return "server took too long to respond"
    if "Connection refused" in text:
        return "server refused the connection"
    if "Max retries exceeded" in text:
        return "could not reach the server after several attempts"
    return "network error"
