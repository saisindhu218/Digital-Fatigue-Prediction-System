from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from src.models.device import DeviceCreate, QRToken, DevicePairingStatus
from src.services.qr_service import QRService
from src.database import db
import uuid

router = APIRouter(prefix="/pairing", tags=["device-pairing"])


# store active user in memory
ACTIVE_USER = {"user_id": None}


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
async def generate_pairing_code():

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

    existing_device = await db.db.devices.find_one({
        "device_id": device_data.device_id,
        "user_id": device_data.user_id
    })

    if existing_device:

        await db.db.devices.update_one(
            {"_id": existing_device["_id"]},
            {"$set": {"last_active": datetime.utcnow()}}
        )

        device_id = existing_device["_id"]

    else:

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
async def get_device_status():

    if not ACTIVE_USER["user_id"]:
        return {
            "laptop": False,
            "mobile": False,
            "last_synced": None,
            "data_points": 0
        }

    devices = await db.db.devices.find(
        {"user_id": ACTIVE_USER["user_id"]}
    ).to_list(100)

    laptop = any(d["device_type"] == "laptop" for d in devices)
    mobile = any(d["device_type"] == "mobile" for d in devices)

    usage_count = await db.db.usage_data.count_documents({
        "user_id": ACTIVE_USER["user_id"]
    })

    return {
        "laptop": laptop,
        "mobile": mobile,
        "last_synced": datetime.utcnow().isoformat(),
        "data_points": usage_count
    }