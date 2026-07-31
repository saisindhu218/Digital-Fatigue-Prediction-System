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

# Where we keep persistent state (token, device id, server url).
if os.name == "nt":
    _base = Path(os.getenv("APPDATA", Path.home()))
else:
    _base = Path.home() / ".config"

CONFIG_DIR = _base / APP_NAME
CONFIG_FILE = CONFIG_DIR / "agent_config.json"

DEFAULT_SERVER_URL = os.getenv("CONGIGUARD_SERVER_URL", "").strip() or None


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
      2. CONGIGUARD_SERVER_URL environment variable
      3. Local dev default (http://localhost:8000) -- if you're pairing
         against a deployed backend, set CONGIGUARD_SERVER_URL once
         before your first `pair`/`login` and it'll be remembered from
         then on.
    """
    cfg = load_config()

    if cfg.get("server_url"):
        return cfg["server_url"].rstrip("/")

    if DEFAULT_SERVER_URL:
        return DEFAULT_SERVER_URL.rstrip("/")

    return "http://localhost:8000"


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
