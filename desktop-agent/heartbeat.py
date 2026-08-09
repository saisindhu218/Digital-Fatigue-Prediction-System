"""
Sends a lightweight "I'm alive" ping every ~30 seconds so the dashboard
can show the laptop as Connected/Offline without depending on how much
activity data has been uploaded yet.
"""

import socket

import requests

import config

AGENT_VERSION = config.AGENT_VERSION


def send_heartbeat() -> bool:
    server_url = config.get_server_url()
    device_id = config.get_or_create_device_id()
    user_id = config.get_user_id()

    if not user_id:
        return False

    try:
        response = requests.post(
            f"{server_url}/api/v1/pairing/heartbeat",
            json={
                "device_id": device_id,
                "user_id": user_id,
                "device_name": socket.gethostname() or "My Laptop",
                "device_type": "laptop",
                "hostname": socket.gethostname(),
                "agent_version": AGENT_VERSION,
            },
            timeout=10,
        )
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"[HEARTBEAT] {config.describe_network_error(e)}")
        return False
