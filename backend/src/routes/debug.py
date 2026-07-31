"""
Debug endpoint for diagnosing fatigue=0 issue
"""

from fastapi import APIRouter, HTTPException
from src.database import db
from src.services.feature_extractor import LiveFeatureExtractor
from src.services.ml_service import ml_service
from src.config import settings
from datetime import datetime, timedelta
import pytz

router = APIRouter(prefix="/debug", tags=["debug"])

IST = pytz.timezone('Asia/Kolkata')
feature_extractor = LiveFeatureExtractor()


def _require_debug_mode():
    """These diagnostic endpoints have no authentication and can return
    other users' raw activity/prediction data -- must stay off on a
    public deploy unless DEBUG_MODE=true is explicitly set."""
    if not settings.DEBUG_MODE:
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/fatigue-diagnostic/{user_id}")
async def fatigue_diagnostic(user_id: str):
    """Check each stage of the fatigue calculation pipeline"""
    _require_debug_mode()

    try:
        ist_now = datetime.now(IST)
        cutoff = ist_now.replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = cutoff.astimezone(pytz.utc)
        
        # Stage 1: Check if activity data exists
        laptop_count = await db.db.usage_data.count_documents({
            "user_id": user_id,
            "data_type": "laptop",
            "timestamp": {"$gte": cutoff}
        })
        
        mobile_count = await db.db.usage_data.count_documents({
            "user_id": user_id,
            "data_type": "mobile",
            "timestamp": {"$gte": cutoff}
        })
        
        # Stage 2: Get recent activity data
        laptop_data = await db.db.usage_data.find({
            "user_id": user_id,
            "data_type": "laptop",
            "timestamp": {"$gte": cutoff}
        }).sort("timestamp", -1).limit(10).to_list(10)
        
        mobile_data = await db.db.usage_data.find({
            "user_id": user_id,
            "data_type": "mobile",
            "timestamp": {"$gte": cutoff}
        }).sort("timestamp", -1).limit(10).to_list(10)
        
        # Stage 3: Extract features from data
        features = feature_extractor.extract_features_from_live_data(
            laptop_data,
            mobile_data,
            user_id
        )
        
        # Stage 4: Calculate fatigue prediction
        fatigue_result = ml_service.predict_fatigue(features)
        
        # Stage 5: Check if prediction is stored in DB
        latest_prediction = await db.db.predictions.find_one({
            "user_id": user_id,
            "timestamp": {"$gte": cutoff}
        }, sort=[("timestamp", -1)])
        
        return {
            "user_id": user_id,
            "diagnostic": {
                "stage_1_activity_data_exists": {
                    "laptop_records": laptop_count,
                    "mobile_records": mobile_count,
                    "total_records": laptop_count + mobile_count
                },
                "stage_2_latest_samples": {
                    "laptop_sample": laptop_data[0] if laptop_data else None,
                    "mobile_sample": mobile_data[0] if mobile_data else None
                },
                "stage_3_extracted_features": features,
                "stage_4_calculated_fatigue": fatigue_result,
                "stage_5_stored_prediction": latest_prediction,
                "summary": {
                    "_Has_Activity_Data": laptop_count + mobile_count > 0,
                    "_Features_Extractable": len(features) > 0,
                    "_Fatigue_Score_Calculated": fatigue_result.get("score", 0) > 0,
                    "_Prediction_Stored_In_DB": latest_prediction is not None
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic error: {str(e)}")


@router.get("/all-diagnostics")
async def all_diagnostics():
    """Check diagnostic info for all users and show recent activity"""
    _require_debug_mode()

    try:
        # Get all users
        all_users = await db.db.users.find({}).to_list(None)
        
        # Get recent activity records across all users
        recent_activity = await db.db.usage_data.find({}).sort("timestamp", -1).limit(20).to_list(20)
        
        # Get recent predictions
        recent_predictions = await db.db.predictions.find({}).sort("timestamp", -1).limit(20).to_list(20)
        
        return {
            "total_users": len(all_users),
            "users": [{"username": u.get("username"), "user_id": str(u.get("_id")), "email": u.get("email")} for u in all_users],
            "recent_activity_records": recent_activity,
            "recent_predictions": recent_predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic error: {str(e)}")
