from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/notifications", tags=["notifications"])

class NotificationBase(BaseModel):
    user_id: str
    title: str
    message: str
    notification_type: str  # fatigue_alert, productivity_alert, recommendation
    priority: str  # low, medium, high
    data: dict = {}

class NotificationCreate(NotificationBase):
    pass

class NotificationInDB(NotificationBase):
    id: str
    created_at: datetime
    read: bool = False
    read_at: datetime = None

@router.post("/send", response_model=NotificationInDB)
async def send_notification(notification: NotificationCreate):
    """Send a notification to user"""
    
    notification_id = str(uuid.uuid4())
    notification_record = {
        "_id": notification_id,
        "user_id": notification.user_id,
        "title": notification.title,
        "message": notification.message,
        "notification_type": notification.notification_type,
        "priority": notification.priority,
        "data": notification.data,
        "created_at": datetime.utcnow(),
        "read": False,
        "read_at": None
    }
    
    # Store in database
    from database import db
    await db.db.notifications.insert_one(notification_record)
    
    # Here you would integrate with:
    # - WebSocket for real-time web notifications
    # - Firebase Cloud Messaging for mobile push notifications
    
    return NotificationInDB(
        id=notification_id,
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        notification_type=notification.notification_type,
        priority=notification.priority,
        data=notification.data,
        created_at=notification_record["created_at"],
        read=False
    )

@router.get("/user/{user_id}", response_model=List[NotificationInDB])
async def get_user_notifications(
    user_id: str, 
    unread_only: bool = False,
    limit: int = 50
):
    """Get notifications for a user"""
    
    from database import db
    
    query = {"user_id": user_id}
    if unread_only:
        query["read"] = False
    
    cursor = db.db.notifications.find(query).sort("created_at", -1).limit(limit)
    notifications = await cursor.to_list(length=limit)
    
    return [
        NotificationInDB(
            id=n["_id"],
            user_id=n["user_id"],
            title=n["title"],
            message=n["message"],
            notification_type=n["notification_type"],
            priority=n["priority"],
            data=n.get("data", {}),
            created_at=n["created_at"],
            read=n.get("read", False),
            read_at=n.get("read_at")
        )
        for n in notifications
    ]

@router.post("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """Mark notification as read"""
    
    from database import db
    
    result = await db.db.notifications.update_one(
        {"_id": notification_id},
        {
            "$set": {
                "read": True,
                "read_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

@router.post("/user/{user_id}/read-all")
async def mark_all_as_read(user_id: str):
    """Mark all notifications as read for a user"""
    
    from database import db
    
    await db.db.notifications.update_many(
        {"user_id": user_id, "read": False},
        {
            "$set": {
                "read": True,
                "read_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "All notifications marked as read"}

@router.delete("/{notification_id}")
async def delete_notification(notification_id: str):
    """Delete a notification"""
    
    from database import db
    
    result = await db.db.notifications.delete_one({"_id": notification_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification deleted"}