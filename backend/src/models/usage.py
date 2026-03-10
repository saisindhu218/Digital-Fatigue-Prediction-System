from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class UsageDataBase(BaseModel):
    device_id: str
    user_id: str
    timestamp: datetime
    session_id: str
    
class LaptopUsageData(UsageDataBase):
    active_app: str
    usage_duration: float  # minutes
    session_length: float  # minutes
    idle_time: float  # minutes
    time_of_day: str  # morning/afternoon/evening/night
    keystrokes: Optional[int] = 0
    mouse_clicks: Optional[int] = 0
    
class MobileUsageData(UsageDataBase):
    app_name: str
    screen_time: float  # minutes
    category: Optional[str] = None
    notifications_received: Optional[int] = 0
    
class PredictionRequest(BaseModel):
    user_id: str
    timestamp: datetime
    features: Dict[str, Any]
    
class PredictionResponse(BaseModel):
    fatigue_score: float
    fatigue_level: str  # Low/Medium/High
    productivity_loss: float  # hours/week
    confidence: float
    peak_hours: List[str]
    fatigue_prone_windows: List[str]
    recommendations: List[str]