from fastapi import APIRouter, HTTPException, status, Depends
from src.models.user import (
    UserPreferences, UserGoals, PreferencesUpdate, GoalsUpdate,
    Notification, NotificationResponse
)
from src.database import db
from pymongo.errors import PyMongoError
from src.routes.auth import get_current_user
from src.services.notification_service import notification_service
from datetime import datetime, timedelta
from typing import List, Any

router = APIRouter(prefix="/users", tags=["user-preferences"])


def _notification_sort_key(notification: dict) -> datetime:
    timestamp = notification.get("timestamp")
    if isinstance(timestamp, datetime):
        return timestamp
    if isinstance(timestamp, str):
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return datetime.min
    return datetime.min


async def _generate_real_data_demo_notifications(user: dict) -> List[dict]:
    """Generate 2-3 notifications from the user's latest real data if list is empty."""
    user_id = user.get("_id")
    if not user_id:
        return []

    preferences = user.get("preferences", {})
    goals = user.get("goals", {})

    now = datetime.utcnow()
    try:
        latest_prediction = await db.db.predictions.find_one(
            {"user_id": user_id},
            sort=[("timestamp", -1)]
        )

        if not latest_prediction:
            return []

        latest_usage = await db.db.usage_data.find_one(
            {"user_id": user_id, "data_type": "laptop"},
            sort=[("timestamp", -1)]
        )
    except PyMongoError as e:
        print(f"❌ DB error in _generate_real_data_demo_notifications for user {user_id}: {e}")
        return []

    generated: List[dict] = []

    fatigue_score = float(latest_prediction.get("fatigue_score", 0))
    fatigue_level = str(latest_prediction.get("fatigue_level", "Moderate"))
    productivity_loss = float(latest_prediction.get("productivity_loss_hours", 0))

    if notification_service.check_fatigue_threshold(fatigue_score, goals) and notification_service.should_send_notification(preferences, "fatigue_alert"):
        generated.append(notification_service.generate_fatigue_alert(fatigue_score, fatigue_level, []))

    if productivity_loss > 1.0:
        generated.append(notification_service.generate_productivity_alert(productivity_loss))

    if latest_usage and notification_service.should_send_notification(preferences, "break"):
        usage_duration = int(latest_usage.get("usage_duration", 0) or 0)
        session_minutes = int(latest_usage.get("session_length_minutes", 0) or 0)
        screen_minutes = max(usage_duration, session_minutes)
        if screen_minutes <= 0:
            screen_minutes = 60
        generated.append(notification_service.generate_break_alert(screen_minutes))

    # Ensure we always return at least two practical demo notifications from real prediction data.
    if len(generated) < 2:
        focus_target = int(goals.get("target_focus_score", 80))
        generated.append(
            notification_service.create_notification(
                title="📌 Focus Target Reminder",
                message=f"Your current fatigue score is {fatigue_score:.0f}%. Keep your next block aligned to your focus target of {focus_target}%.",
                notification_type="recommendation",
                action_url="/recommendations"
            )
        )

    if len(generated) < 3 and notification_service.should_send_notification(preferences, "weekly_digest"):
        try:
            week_cutoff = now - timedelta(days=7)
            recent_prediction_count = await db.db.predictions.count_documents({
                "user_id": user_id,
                "timestamp": {"$gte": week_cutoff}
            })
            generated.append(
                notification_service.generate_weekly_digest(
                    break_count=0,
                    fatigue_alerts=1 if fatigue_score >= 70 else 0,
                    predictions_made=int(recent_prediction_count),
                    insights="Check analytics to review your week-over-week trend."
                )
            )
        except PyMongoError as e:
            print(f"❌ DB error counting predictions for weekly digest for user {user_id}: {e}")

    return generated[:3]

# ========== PREFERENCES ENDPOINTS ==========

@router.get("/me/preferences", response_model=UserPreferences)
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """Get user preferences"""
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        user = await db.db.users.find_one({"_id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        preferences = user.get("preferences", {
            "break_alerts": True,
            "fatigue_alerts": True,
            "weekly_digest": False
        })
        
        return UserPreferences(**preferences)
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in get_user_preferences: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching preferences: {str(e)}")

@router.put("/me/preferences", response_model=UserPreferences)
async def update_user_preferences(
    preferences_update: PreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user preferences"""
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        # Fetch current preferences
        user = await db.db.users.find_one({"_id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_prefs = user.get("preferences", {
            "break_alerts": True,
            "fatigue_alerts": True,
            "weekly_digest": False
        })
        
        # Update only provided fields
        update_data = preferences_update.dict(exclude_unset=True)
        updated_prefs = {**current_prefs, **update_data}
        
        # Save to database
        try:
            await db.db.users.update_one(
                {"_id": current_user["user_id"]},
                {"$set": {"preferences": updated_prefs}}
            )
        except PyMongoError as e:
            print(f"❌ DB write error updating preferences for user {current_user['user_id']}: {e}")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
        
        return UserPreferences(**updated_prefs)
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in update_user_preferences: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating preferences: {str(e)}")

# ========== GOALS ENDPOINTS ==========

@router.get("/me/goals", response_model=UserGoals)
async def get_user_goals(current_user: dict = Depends(get_current_user)):
    """Get user goals"""
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        user = await db.db.users.find_one({"_id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        goals = user.get("goals", {
            "target_focus_score": 80,
            "max_fatigue_threshold": 75,
            "daily_screen_limit_hours": 8.0,
            "preferred_work_slot": "09:00-17:00"
        })
        
        return UserGoals(**goals)
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in get_user_goals: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching goals: {str(e)}")

@router.put("/me/goals", response_model=UserGoals)
async def update_user_goals(
    goals_update: GoalsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user goals"""
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        # Fetch current goals
        user = await db.db.users.find_one({"_id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_goals = user.get("goals", {
            "target_focus_score": 80,
            "max_fatigue_threshold": 75,
            "daily_screen_limit_hours": 8.0,
            "preferred_work_slot": "09:00-17:00"
        })
        
        # Update only provided fields
        update_data = goals_update.dict(exclude_unset=True)
        updated_goals = {**current_goals, **update_data}
        
        # Save to database
        try:
            await db.db.users.update_one(
                {"_id": current_user["user_id"]},
                {"$set": {"goals": updated_goals}}
            )
        except PyMongoError as e:
            print(f"❌ DB write error updating goals for user {current_user['user_id']}: {e}")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
        
        return UserGoals(**updated_goals)
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in update_user_goals: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating goals: {str(e)}")

# ========== NOTIFICATIONS ENDPOINTS ==========

@router.get("/me/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = 20,
    unread_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get user notifications"""
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        user = await db.db.users.find_one({"_id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        notifications = user.get("notifications", [])

        # Seed 2-3 meaningful notifications from real data for first-time/demo users.
        if len(notifications) == 0:
            try:
                seeded_notifications = await _generate_real_data_demo_notifications(user)
                if seeded_notifications:
                    notifications = seeded_notifications
                    try:
                        await db.db.users.update_one(
                            {"_id": current_user["user_id"]},
                            {"$set": {"notifications": notifications}}
                        )
                    except PyMongoError as e:
                        print(f"❌ DB write error seeding notifications for user {current_user['user_id']}: {e}")
            except PyMongoError as e:
                print(f"❌ DB error when generating demo notifications for user {current_user['user_id']}: {e}")
        
        # Filter unread if requested
        if unread_only:
            notifications = [n for n in notifications if not n.get("is_read", False)]
        
        # Sort by timestamp descending and limit
        notifications = sorted(
            notifications,
            key=_notification_sort_key,
            reverse=True
        )[:limit]
        
        return [NotificationResponse(**n) for n in notifications]
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in get_notifications: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")

@router.get("/me/notifications/unread-count")
async def get_unread_notification_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications"""
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        user = await db.db.users.find_one({"_id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        notifications = user.get("notifications", [])
        unread_count = sum(1 for n in notifications if not n.get("is_read", False))
        
        return {"unread_count": unread_count}
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in get_unread_notification_count: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching unread count: {str(e)}")

@router.put("/me/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read"""
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        user = await db.db.users.find_one({"_id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        notifications = user.get("notifications", [])
        found = False
        for notif in notifications:
            if notif.get("notification_id") == notification_id:
                notif["is_read"] = True
                found = True
                break
        
        if not found:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        try:
            await db.db.users.update_one(
                {"_id": current_user["user_id"]},
                {"$set": {"notifications": notifications}}
            )
        except PyMongoError as e:
            print(f"❌ DB write error marking notification read for user {current_user['user_id']}: {e}")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
        
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in mark_notification_as_read: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating notification: {str(e)}")

@router.put("/me/notifications/read-all")
async def mark_all_notifications_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        user = await db.db.users.find_one({"_id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        notifications = user.get("notifications", [])
        for notif in notifications:
            notif["is_read"] = True
        
        try:
            await db.db.users.update_one(
                {"_id": current_user["user_id"]},
                {"$set": {"notifications": notifications}}
            )
        except PyMongoError as e:
            print(f"❌ DB write error marking all notifications read for user {current_user['user_id']}: {e}")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
        
        return {"message": "All notifications marked as read"}
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in mark_all_notifications_as_read: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating notifications: {str(e)}")

@router.delete("/me/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a notification"""
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        user = await db.db.users.find_one({"_id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        notifications = user.get("notifications", [])
        new_notifications = [n for n in notifications if n.get("notification_id") != notification_id]
        
        if len(new_notifications) == len(notifications):
            raise HTTPException(status_code=404, detail="Notification not found")
        
        try:
            await db.db.users.update_one(
                {"_id": current_user["user_id"]},
                {"$set": {"notifications": new_notifications}}
            )
        except PyMongoError as e:
            print(f"❌ DB write error deleting notification for user {current_user['user_id']}: {e}")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
        
        return {"message": "Notification deleted"}
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in delete_notification: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting notification: {str(e)}")

@router.delete("/me/notifications")
async def delete_all_notifications(current_user: dict = Depends(get_current_user)):
    """Delete all notifications"""
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        try:
            await db.db.users.update_one(
                {"_id": current_user["user_id"]},
                {"$set": {"notifications": []}}
            )
        except PyMongoError as e:
            print(f"❌ DB write error deleting all notifications for user {current_user['user_id']}: {e}")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
        
        return {"message": "All notifications deleted"}
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in delete_all_notifications: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting notifications: {str(e)}")

@router.post("/me/notifications")
async def create_notification(
    notification: Notification,
    current_user: dict = Depends(get_current_user)
):
    """Create a new notification (internal use)"""
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        user = await db.db.users.find_one({"_id": current_user["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        notifications = user.get("notifications", [])
        notification_dict = notification.dict()
        notifications.append(notification_dict)
        
        # Keep only last 100 notifications
        notifications = notifications[-100:]
        
        try:
            await db.db.users.update_one(
                {"_id": current_user["user_id"]},
                {"$set": {"notifications": notifications}}
            )
        except PyMongoError as e:
            print(f"❌ DB write error creating notification for user {current_user['user_id']}: {e}")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
        
        return NotificationResponse(**notification_dict)
    except HTTPException:
        raise
    except PyMongoError as e:
        print(f"❌ DB error in create_notification: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating notification: {str(e)}")
