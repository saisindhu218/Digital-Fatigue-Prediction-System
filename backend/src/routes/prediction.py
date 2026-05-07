from fastapi import APIRouter,HTTPException
from datetime import datetime, timedelta, timezone
from src.models.usage import PredictionRequest,PredictionResponse
from src.services.ml_service import ml_service
from src.services.feature_extractor import LiveFeatureExtractor
from src.database import db
import uuid
from pymongo.errors import PyMongoError

router=APIRouter(prefix="/prediction",tags=["predictions"])
feature_extractor=LiveFeatureExtractor()


def utc_now():
    return datetime.now(timezone.utc)

@router.post("/predict",response_model=PredictionResponse, responses={503: {"description": "Database not available"}, 404: {"description": "No usage data available"}, 500: {"description": "Prediction failed"}})
async def predict_fatigue(request:PredictionRequest):

    if db.db is None:
        raise HTTPException(status_code=503,detail="Database not available")

    try:

        cutoff=utc_now()-timedelta(hours=6)

        laptop_data=await db.db.usage_data.find({
            "user_id":request.user_id,
            "data_type":"laptop",
            "timestamp":{"$gte":cutoff}
        }).to_list(200)
        mobile_data=await db.db.usage_data.find({
            "user_id":request.user_id,
            "data_type":"mobile",
            "timestamp":{"$gte":cutoff}
        }).to_list(200)

        
    except PyMongoError as e:
        print(f"❌ DB error in /predict: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")

        if not laptop_data and not mobile_data:
            raise HTTPException(status_code=404,detail="No usage data available")

        features=feature_extractor.extract_features_from_live_data(
            laptop_data,mobile_data,request.user_id
        )

        fatigue_result=ml_service.predict_fatigue(features)

        productivity_loss=ml_service.predict_productivity_loss(
            features
        )

        productivity_score=max(0,100-productivity_loss*5)
        productivity_confidence=ml_service.estimate_productivity_confidence(
            len(laptop_data) + len(mobile_data),
            features.get("productive_ratio", 0.5),
            features.get("focus_score", 50),
            productivity_loss,
        )

        prediction_record={
            "_id":str(uuid.uuid4()),
            "user_id":request.user_id,
            "timestamp":utc_now(),
            "fatigue_score":fatigue_result["score"],
            "fatigue_level":fatigue_result["level"],
            "confidence":fatigue_result["confidence"],
            "productivity_loss_hours":productivity_loss,
            "productivity_score":productivity_score,
            "productivity_confidence":productivity_confidence
        }

        try:
            await db.db.predictions.insert_one(prediction_record)
        except PyMongoError as e:
            print(f"❌ DB write error saving prediction: {e}")
            raise HTTPException(status_code=503, detail="Database temporarily unavailable. Prediction could not be saved.")

        recommendations=generate_recommendations(
            fatigue_result["score"],features,productivity_score
        )

        peak_hours=["09:00-12:00","15:00-17:00"]
        fatigue_windows=["13:00-15:00","22:30-01:00"]

        return PredictionResponse(
            fatigue_score=float(fatigue_result["score"]),
            fatigue_level=fatigue_result["level"],
            productivity_loss=float(productivity_loss),
            confidence=float(fatigue_result["confidence"]),
            peak_hours=peak_hours,
            fatigue_prone_windows=fatigue_windows,
            recommendations=recommendations
        )

    except Exception as e:
        print("Prediction error:",e)
        raise HTTPException(status_code=500,detail="Prediction failed")

def generate_recommendations(fatigue_score,features,productivity_score):

    rec=[]

    if fatigue_score>75:
        rec.append("Take a 20 minute break away from screens")
        rec.append("Avoid intensive cognitive work for the next hour")
        rec.append("Do light stretching or walk for 5 minutes")

    if features["idle_ratio"]>0.4:
        rec.append("Too much idle time detected — consider task batching")

    if features["switches_per_hour"]>25:
        rec.append("High app switching detected — try focus mode")

    if features["productive_ratio"]<0.4:
        rec.append("Low productive app usage detected")

    if features["night_ratio"]>0.25:
        rec.append("Late night usage detected — maintain sleep hygiene")

    if productivity_score<50:
        rec.append("Productivity risk detected — take a structured break")

    if features["screen_time"]>6:
        rec.append("High screen time detected — follow 20-20-20 rule")

    if not rec:
        rec.append("Your current work pattern looks healthy")

    return rec

@router.get("/user/{user_id}/history")
async def get_prediction_history(user_id:str,limit:int=20):
    try:
        predictions=await db.db.predictions.find({
            "user_id":user_id
        }).sort("timestamp",-1).limit(limit).to_list(limit)

        return{
            "user_id":user_id,
            "predictions":predictions,
            "total":len(predictions)
        }
    except PyMongoError as e:
        print(f"❌ DB read error in /prediction/history for user {user_id}: {e}")
        raise HTTPException(status_code=503, detail="Database temporarily unavailable. Please try again later.")