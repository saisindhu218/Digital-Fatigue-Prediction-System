from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

class NotificationService:
    def __init__(self):
        self.thresholds = {
            "fatigue_high": 70,
            "productivity_loss": 10
        }
    
    def create_notification(
        self,
        title: str,
        message: str,
        notification_type: str,
        action_url: Optional[str] = None
    ) -> dict:
        """Create a new notification"""
        return {
            "notification_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "title": title,
            "message": message,
            "type": notification_type,
            "is_read": False,
            "action_url": action_url
        }
    
    def check_fatigue_threshold(self, fatigue_score: float, user_goals: dict = None) -> bool:
        """Check if fatigue score exceeds threshold"""
        threshold = 70
        if user_goals:
            threshold = user_goals.get("max_fatigue_threshold", 70)
        return fatigue_score >= threshold
    
    def check_productivity_threshold(self, productivity_loss: float) -> bool:
        """Check if productivity loss exceeds threshold"""
        return productivity_loss >= self.thresholds["productivity_loss"]
    
    def generate_fatigue_alert(
        self,
        fatigue_score: float,
        fatigue_level: str,
        recommendations: List[str] = None
    ) -> dict:
        """Generate fatigue alert notification"""
        return self.create_notification(
            title="⚠️ High Fatigue Detected",
            message=f"Your fatigue level is {fatigue_level} ({fatigue_score:.0f}%). Consider taking a break to recharge.",
            notification_type="fatigue_alert",
            action_url="/predictions"
        )
    
    def generate_break_alert(self, screen_time_minutes: int) -> dict:
        """Generate break reminder notification"""
        return self.create_notification(
            title="☕ Time for a Break",
            message=f"You've been working for {screen_time_minutes} minutes. Take a 5-10 minute break to stay productive.",
            notification_type="break",
            action_url="/dashboard"
        )
    
    def generate_productivity_alert(self, productivity_loss: float) -> dict:
        """Generate productivity alert notification"""
        return self.create_notification(
            title="📉 Productivity Impact",
            message=f"Estimated productivity loss: {productivity_loss:.1f} hours/week. Check recommendations for improvement.",
            notification_type="productivity_alert",
            action_url="/recommendations"
        )
    
    def generate_recommendation_notification(self, recommendation: str, priority: str) -> dict:
        """Generate recommendation notification"""
        emoji = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
        return self.create_notification(
            title=f"💡 Recommendation {emoji}",
            message=recommendation,
            notification_type="recommendation",
            action_url="/recommendations"
        )
    
    def generate_weekly_digest(
        self,
        break_count: int,
        fatigue_alerts: int,
        predictions_made: int,
        insights: str
    ) -> dict:
        """Generate weekly digest notification"""
        return self.create_notification(
            title="📊 Weekly Fatigue & Productivity Report",
            message=f"This week: {break_count} break reminders, {fatigue_alerts} fatigue alerts, {predictions_made} predictions. {insights}",
            notification_type="weekly_digest",
            action_url="/analytics"
        )
    
    def should_send_notification(self, user_preferences: dict, notification_type: str) -> bool:
        """Check if notification should be sent based on user preferences"""
        if not user_preferences:
            return True
        
        preference_type_map = {
            "break": "break_alerts",
            "fatigue_alert": "fatigue_alerts",
            "weekly_digest": "weekly_digest"
        }
        
        pref_key = preference_type_map.get(notification_type)
        if pref_key:
            return user_preferences.get(pref_key, True)
        
        return True
    
    def filter_notifications_by_preferences(
        self,
        notifications: List[dict],
        user_preferences: dict
    ) -> List[dict]:
        """Filter notifications based on user preferences"""
        return [
            n for n in notifications
            if self.should_send_notification(user_preferences, n.get("type"))
        ]
    
    def mark_as_read(self, notifications: List[dict], notification_id: str) -> List[dict]:
        """Mark a notification as read"""
        for notif in notifications:
            if notif.get("notification_id") == notification_id:
                notif["is_read"] = True
        return notifications
    
    def mark_all_as_read(self, notifications: List[dict]) -> List[dict]:
        """Mark all notifications as read"""
        for notif in notifications:
            notif["is_read"] = True
        return notifications
    
    def delete_notification(self, notifications: List[dict], notification_id: str) -> List[dict]:
        """Delete a notification"""
        return [n for n in notifications if n.get("notification_id") != notification_id]
    
    def get_unread_count(self, notifications: List[dict]) -> int:
        """Get count of unread notifications"""
        return sum(1 for n in notifications if not n.get("is_read", False))
    
    def get_recent_notifications(self, notifications: List[dict], limit: int = 10) -> List[dict]:
        """Get recent notifications sorted by timestamp"""
        sorted_notifs = sorted(
            notifications,
            key=lambda x: x.get("timestamp", datetime.utcnow().isoformat()),
            reverse=True
        )
        return sorted_notifs[:limit]
    
    def process_prediction_for_notifications(
        self,
        fatigue_score: float,
        fatigue_level: str,
        productivity_loss: float,
        screen_time_minutes: int,
        recommendations: List[str],
        user_preferences: dict,
        user_goals: dict
    ) -> List[dict]:
        """Process prediction and generate appropriate notifications based on preferences and goals"""
        notifications = []
        
        # Check fatigue threshold
        if self.check_fatigue_threshold(fatigue_score, user_goals):
            alert = self.generate_fatigue_alert(fatigue_score, fatigue_level, recommendations)
            if self.should_send_notification(user_preferences, "fatigue_alert"):
                notifications.append(alert)
        
        # Check productivity threshold
        if self.check_productivity_threshold(productivity_loss):
            alert = self.generate_productivity_alert(productivity_loss)
            notifications.append(alert)
        
        # Check break time
        if screen_time_minutes > 0 and screen_time_minutes % 60 == 0:
            alert = self.generate_break_alert(screen_time_minutes)
            if self.should_send_notification(user_preferences, "break"):
                notifications.append(alert)
        
        return notifications

notification_service = NotificationService()