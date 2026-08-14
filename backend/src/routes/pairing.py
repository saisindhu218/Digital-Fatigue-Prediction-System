from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timedelta, timezone
from src.models.device import DeviceCreate, QRToken, DevicePairingStatus
from src.services.qr_service import QRService
from src.database import db
from pymongo.errors import PyMongoError
import uuid

from fastapi.responses import RedirectResponse


router = APIRouter(prefix="/pairing", tags=["device-pairing"])

FATIGUE_DASHBOARD_NAME = "FatigueAI Dashboard"


def utc_now():
    return datetime.now(timezone.utc)


def _as_aware_utc(dt):
    """MongoDB/Motor returns naive datetimes by default even though we
    always write timezone-aware UTC ones -- comparing an aware utc_now()
    against a naive value read back from the DB raises 'can't compare
    offset-naive and offset-aware datetimes'. Normalize before comparing."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# store active user in memory
ACTIVE_USER = {"user_id": None}


def is_test_device_record(device_id: str | None = None, device_name: str | None = None) -> bool:
    """Exclude seeded/mock devices from user-facing connected device lists."""
    did = (device_id or "").strip().lower()
    dname = (device_name or "").strip().lower()

    test_markers = ("test", "sample", "mock", "demo")
    return any(marker in did for marker in test_markers) or any(marker in dname for marker in test_markers)


# ---------------- SAVE ACTIVE USER ----------------

@router.post("/save-user", responses={400: {"description": "user_id required"}})
async def save_active_user(data: dict):

    user_id = data.get("user_id")

    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")

    ACTIVE_USER["user_id"] = user_id

    return {
        "message": "Active user saved",
        "user_id": user_id
    }


# ---------------- GET ACTIVE USER ----------------

@router.get("/active-user")
async def get_active_user():

    return {"user_id": ACTIVE_USER["user_id"]}


# ---------------- GENERATE PAIRING CODE ----------------

@router.post("/generate", responses={400: {"description": "Active user not set"}})
async def generate_pairing_code(user_id: str | None = None):

    if user_id:
        ACTIVE_USER["user_id"] = user_id

    if not ACTIVE_USER["user_id"]:
        raise HTTPException(status_code=400, detail="Active user not set")

    pairing_code = str(uuid.uuid4())[:6].upper()

    try:
        await db.db.qr_tokens.insert_one({
            "token": pairing_code,
            "user_id": ACTIVE_USER["user_id"],
            "created_at": utc_now(),
            "expires_at": utc_now() + timedelta(minutes=5)
        })
    except PyMongoError as e:
        print(f"❌ DB error generating pairing code: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")

    return {
        "pairing_code": pairing_code
    }


# ---------------- GENERATE FULL QR (ADVANCED MODE) ----------------

@router.post("/generate-qr", response_model=QRToken)
async def generate_qr_code(device_data: DeviceCreate):

    is_dashboard_placeholder = (
        (device_data.device_name or "") == FATIGUE_DASHBOARD_NAME and
        (device_data.device_id or "").startswith("portal_")
    )

    existing_device = None
    device_id = None

    try:
        if not is_dashboard_placeholder:
            existing_device = await db.db.devices.find_one({
                "device_id": device_data.device_id,
                "user_id": device_data.user_id
            })

        if existing_device:

            await db.db.devices.update_one(
                {"_id": existing_device["_id"]},
                {"$set": {
                    "device_name": device_data.device_name  # Update name if changed
                }}
            )

            device_id = existing_device["_id"]

        elif not is_dashboard_placeholder:

            device_id = str(uuid.uuid4())

            device = {
                "_id": device_id,
                "device_id": device_data.device_id,
                "device_type": device_data.device_type,
                "device_name": device_data.device_name,
                "user_id": device_data.user_id,
                "paired_at": None,
                "pairing_status": DevicePairingStatus.PENDING,
                "last_active": utc_now()
            }

            await db.db.devices.insert_one(device)

        qr_data = QRService.generate_qr_token(
            user_id=device_data.user_id,
            device_type=device_data.device_type
        )

        await db.db.qr_tokens.insert_one({
            "token": qr_data["token"],
            "user_id": device_data.user_id,
            "device_id": device_id,
            "device_type": device_data.device_type,
            "expires_at": qr_data["expires_at"],
            "created_at": utc_now()
        })

        print(f"QR generated for device {device_id} (token={qr_data['token'][:6]}...)")

        
        return {
           "token": qr_data["token"],
           "qr_code_url": qr_data["qr_code_url"],
           "expires_at": qr_data["expires_at"]
        }
    except PyMongoError as e:
        print(f"❌ DB error generating QR code: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")


# ---------------- VERIFY PAIRING ----------------

@router.post("/verify-pairing", responses={404: {"description": "Invalid QR token"}, 410: {"description": "QR token expired"}})
async def verify_pairing(token: str, scanning_device_id: str):

    try:
        qr_token = await db.db.qr_tokens.find_one({"token": token})

        if not qr_token:
            raise HTTPException(status_code=404, detail="Invalid QR token")

        if utc_now() > _as_aware_utc(qr_token["expires_at"]):

            await db.db.qr_tokens.delete_one({"_id": qr_token["_id"]})

            raise HTTPException(status_code=410, detail="QR token expired")

        await db.db.devices.update_one(
            {"device_id": scanning_device_id},
            {
                "$set": {
                    "user_id": qr_token["user_id"],
                    "paired_at": utc_now(),
                    "pairing_status": DevicePairingStatus.PAIRED,
                    "last_active": utc_now()
                },
                "$setOnInsert": {
                    "_id": str(uuid.uuid4()),
                },
            },
            upsert=True,
        )

        await db.db.devices.update_one(
            {"_id": qr_token.get("device_id")},
            {
                "$set": {
                    "paired_at": utc_now(),
                    "pairing_status": DevicePairingStatus.PAIRED,
                    "last_active": utc_now()
                }
            }
        )

        await db.db.qr_tokens.delete_one({"_id": qr_token["_id"]})

        return {
            "message": "Devices paired successfully",
            "user_id": qr_token["user_id"]
        }
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in verify_pairing: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")


# ---------------- DEVICE STATUS (FIX FOR YOUR ERROR) ----------------

@router.get("/status")
async def get_device_status(user_id: str | None = None):

    if not user_id:
        user_id = ACTIVE_USER["user_id"]

    if not user_id:
        return {
            "devices": [],
            "last_synced": None,
            "data_points": 0
        }

    # Define nested async helper functions first
    async def get_first_seen_timestamp(device_id: str | None = None, data_type: str | None = None):
        query = {"user_id": user_id}
        if device_id:
            query["device_id"] = device_id
        if data_type:
            query["data_type"] = data_type

        first_usage = await db.db.usage_data.find_one(query, sort=[("timestamp", 1)])

        if first_usage and first_usage.get("timestamp"):
            return first_usage.get("timestamp").isoformat()

        return None

    async def get_latest_seen_timestamp(device_id: str | None = None, data_type: str | None = None):
        query = {"user_id": user_id}
        if device_id:
            query["device_id"] = device_id
        if data_type:
            query["data_type"] = data_type

        latest_usage_row = await db.db.usage_data.find_one(query, sort=[("timestamp", -1)])

        if latest_usage_row and latest_usage_row.get("timestamp"):
            return latest_usage_row.get("timestamp").isoformat()

        return None

    try:
        # Get all devices for this user
        devices_cursor = db.db.devices.find({"user_id": user_id})
        devices = await devices_cursor.to_list(length=None)

        # Fallback: infer connected devices from recent usage if device docs are missing
        recent_usage_cursor = db.db.usage_data.find({
            "user_id": user_id,
            "timestamp": {"$gte": utc_now() - timedelta(hours=24)}
        })
        recent_usage = await recent_usage_cursor.to_list(length=None)

        if not devices and recent_usage:
            inferred_devices = {}

            for usage in recent_usage:
                device_id = usage.get("device_id")
                if not device_id:
                    continue

                if is_test_device_record(device_id=device_id, device_name=usage.get("device_name")):
                    continue

                fallback_paired_at = await get_first_seen_timestamp(device_id)

                inferred_devices.setdefault(device_id, {
                    "device_id": device_id,
                    "device_name": device_id,
                    "device_type": usage.get("data_type", "unknown"),
                    "status": "connected",
                    "last_active": usage.get("timestamp").isoformat() if usage.get("timestamp") else None,
                    "paired_at": fallback_paired_at,
                })

            return {
                "devices": list(inferred_devices.values()),
                "last_synced": recent_usage[0]["timestamp"].isoformat() if recent_usage and recent_usage[0].get("timestamp") else None,
                "data_points": len(recent_usage)
            }

        # Get latest usage record for last_synced
        latest_usage = await db.db.usage_data.find_one(
            {"user_id": user_id},
            sort=[("timestamp", -1)]
        )

        # Count total data points
        total_data_points = await db.db.usage_data.count_documents({"user_id": user_id})

        recent_cutoff = utc_now() - timedelta(hours=24)

        device_status = []
        for device in devices:
            if (
                (device.get("device_name") or "") == FATIGUE_DASHBOARD_NAME and
                (device.get("device_id") or "").startswith("portal_")
            ):
                continue

            if is_test_device_record(device_id=device.get("device_id"), device_name=device.get("device_name")):
                continue

            # Check if device has recent activity (within last 24 hours)
            recent_activity = await db.db.usage_data.find_one({
                "user_id": user_id,
                "device_id": device.get("device_id"),
                "timestamp": {"$gte": recent_cutoff}
            })

            # Final fallback: trust device heartbeat if last_active itself is recent.
            is_recent_by_last_active = False
            if device.get("last_active"):
                last_active = device.get("last_active")
                # Convert naive to aware if needed
                if last_active.tzinfo is None:
                    last_active = last_active.replace(tzinfo=timezone.utc)
                is_recent_by_last_active = last_active >= recent_cutoff

            fallback_paired_at = None
            if device.get("device_id"):
                fallback_paired_at = await get_first_seen_timestamp(device_id=device.get("device_id"))
            if not fallback_paired_at and device.get("device_type"):
                fallback_paired_at = await get_first_seen_timestamp(data_type=device.get("device_type"))

            resolved_name = device.get("device_name")
            if (not resolved_name or resolved_name == FATIGUE_DASHBOARD_NAME) and recent_activity and recent_activity.get("device_id"):
                resolved_name = recent_activity.get("device_id")
            if not resolved_name:
                resolved_name = f"{device.get('device_type', 'Unknown').title()} Device"

            resolved_last_active = None
            if device.get("device_id"):
                resolved_last_active = await get_latest_seen_timestamp(device_id=device.get("device_id"))
            if not resolved_last_active and device.get("device_type"):
                resolved_last_active = await get_latest_seen_timestamp(data_type=device.get("device_type"))
            if not resolved_last_active and device.get("last_active"):
                resolved_last_active = device.get("last_active").isoformat()

            is_connected = bool(recent_activity or is_recent_by_last_active)

            if device.get("device_type") == "mobile":
                device_state = device.get("status", "disconnected")
            else:
                device_state = "connected" if is_connected else "disconnected"

            device_status.append({
                "device_id": device.get("device_id"),
                "device_name": resolved_name,
                "device_type": device.get("device_type", "unknown"),
                "status": device_state,
                "last_active": resolved_last_active,
                "paired_at": (
                    device.get("paired_at").isoformat()
                    if device.get("paired_at")
                    else fallback_paired_at
                )
            })

        if not device_status and recent_usage:
            inferred_devices = {}

            for usage in recent_usage:
                device_id = usage.get("device_id")
                if not device_id:
                    continue

                if is_test_device_record(device_id=device_id, device_name=usage.get("device_name")):
                    continue

                fallback_paired_at = await get_first_seen_timestamp(device_id)

                inferred_devices.setdefault(device_id, {
                    "device_id": device_id,
                    "device_name": device_id,
                    "device_type": usage.get("data_type", "unknown"),
                    "status": "connected",
                    "last_active": usage.get("timestamp").isoformat() if usage.get("timestamp") else None,
                    "paired_at": fallback_paired_at,
                })

            device_status = list(inferred_devices.values())

        return {
            "devices": device_status,
            "last_synced": latest_usage["timestamp"].isoformat() if latest_usage else None,
            "data_points": total_data_points
        }
    except PyMongoError as e:
        print(f"❌ DB error in get_device_status: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")


    

from fastapi.responses import HTMLResponse

@router.get("/scan", response_class=HTMLResponse)
async def scan_qr(token: str, request: Request):

    try:
        qr_token = await db.db.qr_tokens.find_one({"token": token})

        if not qr_token:
            return "<h2>❌ Invalid QR</h2>"

        if utc_now() > _as_aware_utc(qr_token["expires_at"]):
            return "<h2>⏰ QR Expired</h2>"
    except PyMongoError as e:
        print(f"❌ DB error in scan_qr: {e}")
        return "<h2>❌ Database error. Please try again.</h2>"

    import uuid

    device_id = request.cookies.get("device_id")
    if not device_id:
        device_id = "mobile_" + uuid.uuid4().hex[:8]

    return HTMLResponse(f"""
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Device Pairing</title>
    <style>
        body {{
            margin: 0;
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }}

        .card {{
            background: white;
            padding: 30px;
            border-radius: 16px;
            width: 90%;
            max-width: 350px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        h2 {{
            margin-bottom: 20px;
            color: #333;
        }}

        input {{
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #ccc;
            margin-bottom: 20px;
            font-size: 14px;
        }}

        button {{
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            font-size: 15px;
            cursor: pointer;
            transition: 0.3s;
        }}

        button:hover {{
            opacity: 0.9;
        }}

        .success {{
            color: #4CAF50;
            font-size: 22px;
            font-weight: bold;
        }}

        .sub {{
            margin-top: 10px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>

<body>

<div class="card">

    <h2>📱 Connect Your Device</h2>

    <input id="deviceName" placeholder="Enter device name (e.g. Sindhu's Phone)" />

    <button onclick="connectDevice()">Connect Device</button>

</div>

<script>
    async function connectDevice() {{
        const name = document.getElementById("deviceName").value || "Mobile Device";

        await fetch("/api/v1/pairing/confirm-device", {{
            method: "POST",
            headers: {{
                "Content-Type": "application/json"
            }},
            body: JSON.stringify({{
                token: "{qr_token['token']}",
                device_id: "{device_id}",
                device_name: name
            }})
        }});

        document.body.innerHTML = `
            <div style="display:flex;justify-content:center;align-items:center;height:100vh;
                        background: linear-gradient(135deg, #667eea, #764ba2);">
                <div class="card">
                    <div class="success">✅ Device Connected</div>
                    <div class="sub">${{name}} is now connected</div>
                </div>
            </div>
        `;
    }}
</script>

</body>
</html>
""")


@router.post("/confirm-device", responses={404: {"description": "Invalid token"}})
async def confirm_device(data: dict):

    token = data.get("token")
    device_id = data.get("device_id")
    device_name = data.get("device_name")

    try:
        qr_token = await db.db.qr_tokens.find_one({"token": token})

        if not qr_token:
            raise HTTPException(status_code=404, detail="Invalid token")

        existing = await db.db.devices.find_one({
            "device_id": device_id,
            "user_id": qr_token["user_id"]
        })

        if not existing:
            await db.db.devices.insert_one({
                "device_id": device_id,
                "device_type": "mobile",
                "device_name": device_name,
                "user_id": qr_token["user_id"],
                "paired_at": utc_now(),
                "pairing_status": "paired",
                "last_active": utc_now(),
                "status": "connected"
            })
        else:
            await db.db.devices.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "device_name": device_name,
                        "last_active": utc_now(),
                        "status": "connected"
                    }
                }
            )

        return {"message": "Device connected"}
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in confirm_device: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")

# ---------------- AGENT HEARTBEAT ----------------
# Called every ~30-60s by the desktop agent while it's running in the
# background. This gives a much simpler and more reliable "connected"
# signal than inferring status purely from recent usage_data timestamps.

HEARTBEAT_STALE_SECONDS = 90  # no heartbeat in this window => considered offline


@router.post("/heartbeat", responses={400: {"description": "device_id and user_id required"}})
async def agent_heartbeat(data: dict):

    device_id = data.get("device_id")
    user_id = data.get("user_id")
    device_name = data.get("device_name")
    device_type = data.get("device_type", "laptop")
    hostname = data.get("hostname")
    agent_version = data.get("agent_version")

    if not device_id or not user_id:
        raise HTTPException(status_code=400, detail="device_id and user_id required")

    now = utc_now()

    update_fields = {
        "user_id": user_id,
        "device_type": device_type,
        "last_heartbeat": now,
        "last_active": now,
        "status": "connected",
        "pairing_status": DevicePairingStatus.PAIRED,
    }

    if device_name:
        update_fields["device_name"] = device_name
    if hostname:
        update_fields["hostname"] = hostname
    if agent_version:
        update_fields["agent_version"] = agent_version

    try:
        result = await db.db.devices.update_one(
            {"device_id": device_id},
            {
                "$set": update_fields,
                "$setOnInsert": {
                    "_id": str(uuid.uuid4()),
                    "paired_at": now,
                },
            },
            upsert=True,
        )
    except PyMongoError as e:
        print(f"❌ DB error in agent_heartbeat: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")

    return {
        "message": "heartbeat received",
        "device_id": device_id,
        "server_time": now.isoformat(),
    }


# ---------------- LIVE AGENT STATUS (for dashboard) ----------------
# Lightweight endpoint the frontend can poll to know if the desktop
# agent is currently online, based purely on heartbeat recency.

@router.get("/agent-status")
async def agent_status(user_id: str):

    if not user_id:
        return {"devices": []}

    cutoff = utc_now() - timedelta(seconds=HEARTBEAT_STALE_SECONDS)

    try:
        devices_cursor = db.db.devices.find({"user_id": user_id})
        devices = await devices_cursor.to_list(length=None)
    except PyMongoError as e:
        print(f"❌ DB error in agent_status: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")

    results_by_device_id = {}
    for device in devices:
        if is_test_device_record(device_id=device.get("device_id"), device_name=device.get("device_name")):
            continue

        device_id = device.get("device_id")
        if not device_id:
            continue

        last_heartbeat = device.get("last_heartbeat")
        online = False
        if last_heartbeat:
            hb = last_heartbeat
            if hb.tzinfo is None:
                hb = hb.replace(tzinfo=timezone.utc)
            online = hb >= cutoff

        entry = {
            "device_id": device_id,
            "device_name": device.get("device_name") or device_id,
            "device_type": device.get("device_type", "unknown"),
            "hostname": device.get("hostname"),
            "agent_version": device.get("agent_version"),
            "online": online,
            "last_heartbeat": last_heartbeat.isoformat() if last_heartbeat else None,
        }

        existing = results_by_device_id.get(device_id)
        if existing is None:
            results_by_device_id[device_id] = entry
        elif online and not existing["online"]:
            results_by_device_id[device_id] = entry
        elif online == existing["online"]:
            existing_hb = existing["last_heartbeat"] or ""
            new_hb = entry["last_heartbeat"] or ""
            if new_hb > existing_hb:
                results_by_device_id[device_id] = entry

    return {"devices": list(results_by_device_id.values())}


@router.post("/disconnect", responses={404: {"description": "Device not found"}})
async def disconnect_device(device_id: str):

    try:
        device = await db.db.devices.find_one({"device_id": device_id})

        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        await db.db.devices.update_one(
            {"_id": device["_id"]},
            {
                "$set": {
                    "status": "disconnected",
                    "last_active": utc_now()
                }
            }
        )

        return {"message": "Device disconnected"}
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in disconnect_device: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")    