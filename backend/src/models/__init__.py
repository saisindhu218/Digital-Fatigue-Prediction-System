"""
Models package for Digital Fatigue Guard
"""

from .device import (
    DeviceCreate, DeviceInDB, QRToken, 
    DevicePairingStatus, DeviceType, DeviceBase
)
from .user import (
    User, UserCreate, UserInDB, UserUpdate, 
    UserLogin, Token, TokenData
)
from .usage import (
    UsageDataBase, LaptopUsageData, MobileUsageData,
    PredictionRequest, PredictionResponse
)

__all__ = [
    # Device models
    "DeviceCreate", "DeviceInDB", "QRToken", 
    "DevicePairingStatus", "DeviceType", "DeviceBase",
    
    # User models
    "User", "UserCreate", "UserInDB", "UserUpdate",
    "UserLogin", "Token", "TokenData",
    
    # Usage models
    "UsageDataBase", "LaptopUsageData", "MobileUsageData",
    "PredictionRequest", "PredictionResponse"
]