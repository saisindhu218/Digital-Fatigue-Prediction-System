from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from src.models.device import DeviceCreate, QRToken, DevicePairingStatus
from src.services.qr_service import QRService
from src.database import db
import uuid

router = APIRouter(prefix="/pairing", tags=["device-pairing"])


# store active user in memory
ACTIVE_USER = {"user_id": None}


def is_test_device_record(device_id: str | None = None, device_name: str | None = None) -> bool:
    """Exclude seeded/mock devices from user-facing connected device lists."""
    did = (device_id or "").strip().lower()
    dname = (device_name or "").strip().lower()

    test_markers = ("test", "sample", "mock", "demo")
    return any(marker in did for marker in test_markers) or any(marker in dname for marker in test_markers)


# ---------------- SAVE ACTIVE USER ----------------

@router.post("/save-user")
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

@router.post("/generate")
async def generate_pairing_code(user_id: str | None = None):

    if user_id:
        ACTIVE_USER["user_id"] = user_id

    if not ACTIVE_USER["user_id"]:
        raise HTTPException(status_code=400, detail="Active user not set")

    pairing_code = str(uuid.uuid4())[:6].upper()

    await db.db.qr_tokens.insert_one({
        "token": pairing_code,
        "user_id": ACTIVE_USER["user_id"],
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=5)
    })

    return {
        "pairing_code": pairing_code
    }


# ---------------- GENERATE FULL QR (ADVANCED MODE) ----------------

@router.post("/generate-qr", response_model=QRToken)
async def generate_qr_code(device_data: DeviceCreate):

    is_dashboard_placeholder = (
        (device_data.device_name or "") == "FatigueAI Dashboard" and
        (device_data.device_id or "").startswith("portal_")
    )

    existing_device = None
    device_id = None

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
            "last_active": datetime.utcnow()
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
        "created_at": datetime.utcnow()
    })

    return QRToken(
        token=qr_data["token"],
        qr_code_url=qr_data["qr_code_url"],
        expires_at=qr_data["expires_at"]
    )


# ---------------- VERIFY PAIRING ----------------

@router.post("/verify-pairing")
async def verify_pairing(token: str, scanning_device_id: str):

    qr_token = await db.db.qr_tokens.find_one({"token": token})

    if not qr_token:
        raise HTTPException(status_code=404, detail="Invalid QR token")

    if datetime.utcnow() > qr_token["expires_at"]:

        await db.db.qr_tokens.delete_one({"_id": qr_token["_id"]})

        raise HTTPException(status_code=410, detail="QR token expired")

    await db.db.devices.update_one(
        {"device_id": scanning_device_id},
        {
            "$set": {
                "user_id": qr_token["user_id"],
                "paired_at": datetime.utcnow(),
                "pairing_status": DevicePairingStatus.PAIRED,
                "last_active": datetime.utcnow()
            }
        }
    )

    await db.db.devices.update_one(
        {"_id": qr_token.get("device_id")},
        {
            "$set": {
                "paired_at": datetime.utcnow(),
                "pairing_status": DevicePairingStatus.PAIRED,
                "last_active": datetime.utcnow()
            }
        }
    )

    await db.db.qr_tokens.delete_one({"_id": qr_token["_id"]})

    return {
        "message": "Devices paired successfully",
        "user_id": qr_token["user_id"]
    }


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

    # Get all devices for this user
    devices_cursor = db.db.devices.find({"user_id": user_id})
    devices = await devices_cursor.to_list(length=None)

    # Fallback: infer connected devices from recent usage if device docs are missing
    recent_usage_cursor = db.db.usage_data.find({
        "user_id": user_id,
        "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=24)}
    })
    recent_usage = await recent_usage_cursor.to_list(length=None)

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

    recent_cutoff = datetime.utcnow() - timedelta(hours=24)

    device_status = []
    for device in devices:
        if (
            (device.get("device_name") or "") == "FatigueAI Dashboard" and
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
            is_recent_by_last_active = device.get("last_active") >= recent_cutoff

        fallback_paired_at = None
        if device.get("device_id"):
            fallback_paired_at = await get_first_seen_timestamp(device_id=device.get("device_id"))
        if not fallback_paired_at and device.get("device_type"):
            fallback_paired_at = await get_first_seen_timestamp(data_type=device.get("device_type"))

        resolved_name = device.get("device_name")
        if (not resolved_name or resolved_name == "FatigueAI Dashboard") and recent_activity and recent_activity.get("device_id"):
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

        device_status.append({
            "device_id": device.get("device_id"),
            "device_name": resolved_name,
            "device_type": device.get("device_type", "unknown"),
            "status": "connected" if (recent_activity or is_recent_by_last_active) else "disconnected",
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