from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

# ========== PREFERENCES & GOALS ==========
class UserPreferences(BaseModel):
    break_alerts: bool = True
    fatigue_alerts: bool = True
    weekly_digest: bool = False

class UserGoals(BaseModel):
    target_focus_score: int = Field(80, ge=0, le=100)
    max_fatigue_threshold: int = Field(75, ge=0, le=100)
    daily_screen_limit_hours: float = Field(8.0, ge=0, le=24)
    preferred_work_slot: str = "09:00-17:00"

# ========== NOTIFICATIONS ==========
class Notification(BaseModel):
    notification_id: str
    timestamp: datetime
    title: str
    message: str
    type: str  # "break", "fatigue", "prediction", "recommendation"
    is_read: bool = False
    action_url: Optional[str] = None

class NotificationResponse(BaseModel):
    notification_id: str
    timestamp: datetime
    title: str
    message: str
    type: str
    is_read: bool
    action_url: Optional[str] = None

# ========== USER MODELS ==========
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=72)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(UserBase):
    id: str
    created_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True

class User(UserBase):
    """Complete User model with all fields"""
    id: str
    created_at: datetime
    is_active: bool = True
    hashed_password: Optional[str] = None
    devices: List[str] = []
    role: str = "user"
    preferences: Optional[UserPreferences] = UserPreferences()
    goals: Optional[UserGoals] = UserGoals()
    notifications: List[Notification] = []
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class PreferencesUpdate(BaseModel):
    break_alerts: Optional[bool] = None
    fatigue_alerts: Optional[bool] = None
    weekly_digest: Optional[bool] = None

class GoalsUpdate(BaseModel):
    target_focus_score: Optional[int] = Field(None, ge=0, le=100)
    max_fatigue_threshold: Optional[int] = Field(None, ge=0, le=100)
    daily_screen_limit_hours: Optional[float] = Field(None, ge=0, le=24)
    preferred_work_slot: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: Optional[str] = None
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str