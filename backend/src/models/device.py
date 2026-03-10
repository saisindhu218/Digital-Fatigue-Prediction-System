from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum

class DeviceType(str, Enum):
    LAPTOP = "laptop"
    MOBILE = "mobile"

class DevicePairingStatus(str, Enum):
    PENDING = "pending"
    PAIRED = "paired"
    EXPIRED = "expired"

class DeviceBase(BaseModel):
    device_id: str
    device_type: DeviceType
    device_name: str
    
class DeviceCreate(DeviceBase):
    user_id: str
    
class DeviceInDB(DeviceBase):
    id: str
    user_id: str
    paired_at: Optional[datetime]
    pairing_status: DevicePairingStatus
    last_active: datetime
    
class QRToken(BaseModel):
    token: str
    qr_code_url: str
    expires_at: datetime