from datetime import datetime
from typing import Dict, Any
from models.usage import PredictionResponse
from routes.notifications import NotificationCreate

class NotificationService:
    def __init__(self):
        self.thresholds = {
            "fatigue_high": 70,
            "productivity_loss": 10
        }
    
    def check_fatigue_threshold(self, prediction: PredictionResponse) -> bool:
        """Check if fatigue score exceeds threshold"""
        return prediction.fatigue_score >= self.thresholds["fatigue_high"]
    
    def check_productivity_threshold(self, prediction: PredictionResponse) -> bool:
        """Check if productivity loss exceeds threshold"""
        return prediction.productivity_loss >= self.thresholds["productivity_loss"]
    
    def generate_fatigue_alert(self, user_id: str, prediction: PredictionResponse) -> NotificationCreate:
        """Generate fatigue alert notification"""
        return NotificationCreate(
            user_id=user_id,
            title="⚠️ High Fatigue Alert",
            message=f"Your fatigue level is {prediction.fatigue_level} ({prediction.fatigue_score:.0f}%). "
                   f"Consider taking a break.",
            notification_type="fatigue_alert",
            priority="high",
            data={
                "fatigue_score": prediction.fatigue_score,
                "fatigue_level": prediction.fatigue_level,
                "recommendations": prediction.recommendations[:2]
            }
        )
    
    def generate_productivity_alert(self, user_id: str, prediction: PredictionResponse) -> NotificationCreate:
        """Generate productivity alert notification"""
        return NotificationCreate(
            user_id=user_id,
            title="📉 Productivity Warning",
            message=f"Productivity loss estimate: {prediction.productivity_loss:.1f} hours/week. "
                   f"Check recommendations for improvement.",
            notification_type="productivity_alert",
            priority="medium",
            data={
                "productivity_loss": prediction.productivity_loss,
                "peak_hours": prediction.peak_hours,
                "fatigue_windows": prediction.fatigue_prone_windows
            }
        )
    
    def generate_recommendation_notification(self, user_id: str, recommendations: list) -> NotificationCreate:
        """Generate recommendation notification"""
        return NotificationCreate(
            user_id=user_id,
            title="💡 Personalized Recommendation",
            message=recommendations[0] if recommendations else "Take regular breaks for better productivity",
            notification_type="recommendation",
            priority="low",
            data={"recommendations": recommendations}
        )
    
    def process_prediction_for_notifications(self, user_id: str, prediction: PredictionResponse) -> list:
        """Process prediction and generate appropriate notifications"""
        notifications = []
        
        # Check fatigue threshold
        if self.check_fatigue_threshold(prediction):
            notifications.append(self.generate_fatigue_alert(user_id, prediction))
        
        # Check productivity threshold
        if self.check_productivity_threshold(prediction):
            notifications.append(self.generate_productivity_alert(user_id, prediction))
        
        # Always include at least one recommendation
        if prediction.recommendations:
            notifications.append(
                self.generate_recommendation_notification(user_id, prediction.recommendations)
            )
        
        return notifications

notification_service = NotificationService()