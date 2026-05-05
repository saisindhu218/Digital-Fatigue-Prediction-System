# ---------------- IN-BROWSER ACTIVITY LOGGING (WEB) ----------------

from fastapi import APIRouter, Request, HTTPException
from datetime import datetime
import uuid
from src.database import db

# Create router instance if missing
# router = APIRouter()

router = APIRouter(prefix="/usage", tags=["usage"])

@router.post("/user/{user_id}/activity")
async def log_web_activity(user_id: str, payload: dict, request: Request):
    """
    Receives activity events from the web app (browser).
    Expects: { events: [ {type, ts, ...}, ... ] }
    """
    events = payload.get("events", [])
    if not events:
        return {"status": "no events"}

    docs = []
    now = datetime.utcnow()
    for event in events:
        doc = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "timestamp": event.get("ts", now),
            "event_type": event.get("type"),
            "event_data": {k: v for k, v in event.items() if k not in ("ts", "type")},
            "source": "web"
        }
        docs.append(doc)

    try:
        if docs:
            await db.db.usage_data.insert_many(docs)
        return {"status": "ok", "inserted": len(docs)}
    except Exception as e:
        print("❌ Web activity log error:", e)
        raise HTTPException(status_code=500, detail="Failed to log activity events")

from datetime import datetime, timedelta, timezone
from src.database import db
from src.services.feature_extractor import LiveFeatureExtractor
from src.services.ml_service import ml_service
import uuid
import pytz
from pymongo.errors import PyMongoError


feature_extractor = LiveFeatureExtractor()

ist = pytz.timezone("Asia/Kolkata")


# ---------------- HELPER ----------------

async def resolve_user(device_id: str):

    device = await db.db.devices.find_one({"device_id": device_id})

    if device and device.get("user_id"):
        return device.get("user_id")

    # 🔥 AUTO-FIX: get user from latest login/session
    user = await db.db.users.find_one({}, sort=[("created_at", -1)])

    if user:
        user_id = user.get("_id")

        # save mapping automatically
        await db.db.devices.insert_one({
            "device_id": device_id,
            "user_id": user_id,
            "linked_at": datetime.utcnow()
        })

        print(f"✅ Device mapped automatically: {device_id} → {user_id}")

        return user_id

    print("❌ No user found")
    return None


# ---------------- LAPTOP DATA ----------------

@router.post("/laptop")
async def receive_laptop_usage(data: dict):

    device_id = data.get("device_id")
    user_id = data.get("user_id") or await resolve_user(device_id)

    record = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "device_id": device_id,
        "session_id": data.get("session_id"),
        "timestamp": datetime.utcnow(),
        "data_type": "laptop",
        "active_app": data.get("active_app"),
        "app_category": data.get("app_category"),
        "usage_duration": data.get("usage_duration", 1),
        "session_length_minutes": data.get("session_length_minutes", 0),
        "idle_time_seconds": data.get("idle_time_seconds", 0),
        "keystrokes": data.get("keystrokes", 0),
        "mouse_clicks": data.get("mouse_clicks", 0),
        "mouse_moves": data.get("mouse_moves", 0),
        "app_switches": data.get("app_switches", 0),
        "time_of_day": data.get("time_of_day")
    }

    await db.db.usage_data.insert_one(record)

    if user_id:
        await run_prediction(user_id)

    return {"status": "ok"}


# ---------------- LAPTOP BATCH ----------------

@router.post("/laptop/batch")
async def receive_laptop_batch(payload: dict):

    records = payload.get("records", [])
    inserted = 0
    resolved_user = None

    for r in records:

        device_id = r.get("device_id")
        user_id = r.get("user_id") or await resolve_user(device_id)

        resolved_user = user_id

        record = {
            "_id": str(uuid.uuid4()),
            "user_id": user_id,
            "device_id": device_id,
            "session_id": r.get("session_id"),
            "timestamp": datetime.utcnow(),
            "data_type": "laptop",
            "active_app": r.get("active_app"),
            "app_category": r.get("app_category"),
            "usage_duration": r.get("usage_duration", 1),
            "session_length_minutes": r.get("session_length_minutes", 0),
            "idle_time_seconds": r.get("idle_time_seconds", 0),
            "keystrokes": r.get("keystrokes", 0),
            "mouse_clicks": r.get("mouse_clicks", 0),
            "mouse_moves": r.get("mouse_moves", 0),
            "app_switches": r.get("app_switches", 0),
            "time_of_day": r.get("time_of_day")
        }

        await db.db.usage_data.insert_one(record)
        inserted += 1

    if inserted > 0 and resolved_user:
        await run_prediction(resolved_user)

    return {"status": "ok", "records_inserted": inserted}


# ---------------- MOBILE DATA ----------------

@router.post("/mobile")
async def receive_mobile_usage(data: dict):

    device_id = data.get("device_id")
    user_id = data.get("user_id") or await resolve_user(device_id)
    
    record = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "device_id": device_id,
        "timestamp": datetime.utcnow(),
        "data_type": "mobile",
        "app_name": data.get("app_name"),
        "screen_time": data.get("screen_time"),
        "notifications_received": data.get("notifications_received")
    }

    await db.db.usage_data.insert_one(record)

    if user_id:
        await run_prediction(user_id)

    return {"status": "ok"}


# ---------------- RUN ML PREDICTION ----------------

async def run_prediction(user_id: str):

    now_utc = datetime.utcnow()
    recent_cutoff = now_utc - timedelta(minutes=60)
    day_cutoff = now_utc - timedelta(days=1)

    # Primary window: recent 60 minutes to make each 10-minute aggregate affect prediction quickly.
    recent_laptop = await db.db.usage_data.find({
        "user_id": user_id,
        "data_type": "laptop",
        "timestamp": {"$gte": recent_cutoff}
    }).sort("timestamp", -1).limit(200).to_list(200)

    recent_mobile = await db.db.usage_data.find({
        "user_id": user_id,
        "data_type": "mobile",
        "timestamp": {"$gte": recent_cutoff}
    }).sort("timestamp", -1).limit(200).to_list(200)

    # Fallback to a broader window only when recent data is too sparse.
    if len(recent_laptop) + len(recent_mobile) >= 2:
        laptop_data = recent_laptop
        mobile_data = recent_mobile
        prediction_window = "60m"
    else:
        laptop_data = await db.db.usage_data.find({
            "user_id": user_id,
            "data_type": "laptop",
            "timestamp": {"$gte": day_cutoff}
        }).sort("timestamp", -1).limit(500).to_list(500)

        mobile_data = await db.db.usage_data.find({
            "user_id": user_id,
            "data_type": "mobile",
            "timestamp": {"$gte": day_cutoff}
        }).sort("timestamp", -1).limit(500).to_list(500)
        prediction_window = "24h"

    features = feature_extractor.extract_features_from_live_data(
        laptop_data,
        mobile_data,
        user_id
    )

    fatigue_result = ml_service.predict_fatigue(features)

    productivity_loss = ml_service.predict_productivity_loss(features)

    productivity_score = max(0, 100 - productivity_loss * 5)
    productivity_confidence = ml_service.estimate_productivity_confidence(
        len(laptop_data) + len(mobile_data),
        features.get("productive_ratio", 0.5),
        features.get("focus_score", 50),
        productivity_loss,
    )

    recommendations = ml_service.generate_recommendations(
        features,
        fatigue_result,
        productivity_loss
    )

    prediction_record = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "timestamp": datetime.utcnow(),
        "prediction_window": prediction_window,
        "sample_count": len(laptop_data) + len(mobile_data),
        "fatigue_level": fatigue_result["level"],
        "fatigue_score": fatigue_result["score"],
        "confidence": fatigue_result["confidence"],
        "productivity_loss_hours": productivity_loss,
        "productivity_score": productivity_score,
        "productivity_confidence": productivity_confidence,
        "recommendations": recommendations
    }

    try:
        await db.db.predictions.insert_one(prediction_record)
        print("✅ Prediction stored")

    except Exception as e:
        print("❌ Prediction insert error:", e)
        

# ---------------- DASHBOARD DATA ----------------

@router.get("/user/{user_id}/recent")
async def get_recent_usage(user_id: str, hours: int = 24):

    ist_now = datetime.now(pytz.timezone("Asia/Kolkata"))

    cutoff = ist_now.replace(hour=0, minute=0, second=0, microsecond=0)

    # convert cutoff to UTC for DB comparison 
    cutoff = cutoff.astimezone(pytz.utc)

    try:
        laptop_data = await db.db.usage_data.find({
            "user_id": user_id,
            "data_type": "laptop",
            "timestamp": {"$gte": cutoff}
        }).to_list(None)

        mobile_data = await db.db.usage_data.find({
            "user_id": user_id,
            "data_type": "mobile",
            "timestamp": {"$gte": cutoff}
        }).to_list(None)

        predictions = await db.db.predictions.find({
            "user_id": user_id,
            "timestamp": {"$gte": cutoff}   # 🔥 same cutoff as usage_data
        }).sort("timestamp", -1).limit(1).to_list(1)
    except PyMongoError as e:
        print(f"❌ DB read error in /recent for user {user_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database is temporarily unavailable. Please retry in a few seconds."
        )
    
    if not laptop_data and not mobile_data:
        print("⚠️ No data for prediction")

        return {
            "summary": {
                "total_screen_time": 0,
                "total_sessions": 0,
                "avg_session_length": 0,
                "most_used_app": "None",
                "focus_score": 0,
                "break_frequency": 0,
                "peak_hours": "None"
            },
            "predictions": {
                "fatigue": {
                    "fatigue_level": "Low",
                    "fatigue_score": 0,
                    "confidence": 0
                },
                "productivity": {
                    "productivity_score": 0,
                    "productivity_loss_hours": 0,
                    "productivity_confidence": 0,
                    "breakdown": {}
                }
            },
            "recommendations": [],
            "laptop_usage": [],
            "mobile_usage": []
        }
    
    # ✅ FIX
    laptop = laptop_data
    mobile = mobile_data
    # -------- SUMMARY --------


    total_minutes = sum(
        (u.get("usage_duration", 0) or 0)
        for u in laptop
    )

    total_screen_time = round(total_minutes / 60, 2)

    total_sessions = len(set(
        u.get("session_id") for u in laptop if u.get("session_id")
    ))

    avg_session_length = 0
    if laptop:
        avg_session_length = sum(
            (u.get("session_length_minutes", 0) or 0) for u in laptop
        ) / len(laptop)

    most_used_app = "None"

    if laptop:
        app_time = {}

        for u in laptop:
            app = u.get("active_app", "Unknown")
            app_time[app] = app_time.get(app, 0) + (u.get("usage_duration", 0) )

        most_used_app = max(app_time, key=app_time.get)

    focus_score = max(0, min(100, 100 - total_sessions))


    summary = {
        "total_screen_time": round(total_screen_time, 2),
        "total_sessions": total_sessions,
        "avg_session_length": round(avg_session_length, 2),
        "most_used_app": most_used_app,
        "focus_score": focus_score,
        "break_frequency": max(1, int(total_sessions / 5)),
        "peak_hours": "Afternoon"
    }


    # -------- DEFAULT VALUES --------

    fatigue = {
        "fatigue_level": "Medium",
        "fatigue_score": 50,
        "confidence": 80
    }

    productivity = {
        "productivity_score": 75,
        "productivity_loss_hours": 2,
        "breakdown": {
            "Context Switching": 1,
            "Distractions": 0.5,
            "Fatigue": 0.5
        }
    }

    recommendations = []


    # -------- APPLY ML RESULTS --------

    if predictions:

        p = predictions[0]

        fatigue = {
            "fatigue_level": p.get("fatigue_level"),
            "fatigue_score": p.get("fatigue_score"),
            "confidence": round(p.get("confidence", 0) * 100, 2)
        }

        # 🔥 REAL BREAKDOWN CALCULATION

        total_idle = sum(u.get("idle_time_seconds", 0) for u in laptop)
        total_switches = sum(u.get("app_switches", 0) for u in laptop)

        non_productive = sum(
            u.get("usage_duration", 0)
            for u in laptop
            if u.get("app_category") != "HIGH"
        )

        fatigue_hours = round(total_idle / 3600, 2)
        context_hours = round(total_switches / 60, 2) 
        distraction_hours = round(non_productive / 60, 2)

        features = feature_extractor.extract_features_from_live_data(
            laptop,
            mobile,
            user_id
        )

        productivity = {
            "productivity_score": p.get("productivity_score"),
            "productivity_loss_hours": p.get("productivity_loss_hours"),
            "confidence": p.get(
                "productivity_confidence",
                ml_service.estimate_productivity_confidence(
                    len(laptop),
                    features.get("productive_ratio", 0.5),
                    features.get("focus_score", 50),
                    p.get("productivity_loss_hours", 0),
                ),
            ),
            "breakdown": {
                "Fatigue": fatigue_hours,
                "Context Switching": context_hours,
                "Distractions": distraction_hours
            }
        }

        snapshot_recommendations = p.get("recommendations")
        if isinstance(snapshot_recommendations, list) and snapshot_recommendations:
            recommendations = snapshot_recommendations
        else:
            recommendations = ml_service.generate_recommendations(
                features,
                {
                    "level": fatigue["fatigue_level"],
                    "score": fatigue["fatigue_score"]
                },
                productivity["productivity_loss_hours"]
            )


    return {
        "summary": summary,
        "predictions": {
            "fatigue": fatigue,
            "productivity": productivity
        },
        "recommendations": recommendations,
        "laptop_usage": laptop,
        "mobile_usage": mobile
    }

@router.get("/user/{user_id}/trends")
async def get_trends(user_id: str, days: int = 7, offset_days: int = 0):

    # Use IST timezone to match frontend expectations.
    ist_now = datetime.now(pytz.timezone("Asia/Kolkata"))
    offset_days = max(0, offset_days)

    # For days=1, allow requesting an older calendar day window (e.g. yesterday).
    if days == 1:
        day_start_ist = ist_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=offset_days)
        day_end_ist = day_start_ist + timedelta(days=1)
        cutoff = day_start_ist.astimezone(pytz.utc)
        end_cutoff = day_end_ist.astimezone(pytz.utc)
        query_filter = {
            "user_id": user_id,
            "timestamp": {
                "$gte": cutoff,
                "$lt": end_cutoff
            }
        }
    else:
        # For multi-day views, keep existing behavior and ignore offset.
        cutoff_ist = ist_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days-1)
        cutoff = cutoff_ist.astimezone(pytz.utc)
        query_filter = {
            "user_id": user_id,
            "timestamp": {"$gte": cutoff}
        }

    try:
        preds = await db.db.predictions.find(query_filter).sort("timestamp", 1).to_list(200)
    except PyMongoError as e:
        print(f"❌ DB read error in /trends for user {user_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database is temporarily unavailable. Please retry in a few seconds."
        )

    fatigue_trend = []
    productivity_trend = []

    if not preds:
        return {
            "fatigueTrend": [],
            "productivityTrend": []
        }

    # -------- CASE 1: HOURLY DATA FOR TODAY (days=1) --------
    if days == 1:

        time_groups = {}

        for p in preds:
            local_time = p["timestamp"].replace(tzinfo=pytz.utc).astimezone(ist)
            time_label = local_time.strftime("%H:%M")
            
            if time_label not in time_groups:
                time_groups[time_label] = {"fatigue": [], "productivity": []}

            time_groups[time_label]["fatigue"].append(p.get("fatigue_score", 0))
            time_groups[time_label]["productivity"].append(p.get("productivity_score", 0))


        for time_label in sorted(time_groups.keys()):
            values = time_groups[time_label]

            fatigue_trend.append({
                "day": time_label,
                "score": round(sum(values["fatigue"]) / len(values["fatigue"]), 2)
            })

            productivity_trend.append({
                "day": time_label,
                "score": round(sum(values["productivity"]) / len(values["productivity"]), 2)
            })
    # -------- CASE 2: DAILY DATA FOR MULTIPLE DAYS --------
    else:

        daily = {}

        for p in preds:
            local_time = p["timestamp"].replace(tzinfo=pytz.utc).astimezone(ist)
            day = local_time.strftime("%Y-%m-%d")

            if day not in daily:
                daily[day] = {"fatigue": [], "productivity": []}

            daily[day]["fatigue"].append(p.get("fatigue_score", 0))
            daily[day]["productivity"].append(p.get("productivity_score", 0))

        # generate all last N days (using IST)
        all_days = [
            (ist_now - timedelta(days=i)).strftime("%Y-%m-%d")
             for i in range(days-1, -1, -1)
        ]

        for day in all_days:
            if day in daily:
                values = daily[day]
                fatigue_score = round(sum(values["fatigue"]) / len(values["fatigue"]), 2)
                productivity_score = round(sum(values["productivity"]) / len(values["productivity"]), 2)

                fatigue_trend.append({
                    "day": day,
                    "score": fatigue_score
                })

                productivity_trend.append({
                    "day": day,
                    "score": productivity_score
                })
            else:
                # 🔥 fill missing days
                fatigue_trend.append({
                    "day": day,
                    "score": 0
                })

                productivity_trend.append({
                    "day": day,
                    "score": 0
                })          

    return {
        "fatigueTrend": fatigue_trend,
        "productivityTrend": productivity_trend
    }

@router.get("/user/{user_id}/analytics")
async def get_analytics(user_id: str):
    
    # 🔥 Use IST for cutoff to ensure we get all data from last 7 calendar days
    ist_now = datetime.now(ist)
    cutoff_ist = ist_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    cutoff_utc = cutoff_ist.astimezone(pytz.utc)

    records = await db.db.usage_data.find({
        "user_id": user_id,
        "data_type": "laptop",
        "timestamp": {"$gte": cutoff_utc}
    }).to_list(2000)
    
    if not records:
        return {}

    # -------- FILTER & PREPARE --------
    filtered = records  # Use all records from cutoff

    # -------- AVG DAILY (Include all 7 days, even zeros) --------
    from collections import defaultdict

    daily_usage = defaultdict(int)
    
    # Initialize all 7 days with 0
    for i in range(7):
        day_date = (ist_now - timedelta(days=i)).date()
        daily_usage[day_date] = 0

    for r in filtered:
        d = r["timestamp"].replace(tzinfo=pytz.utc).astimezone(ist).date()
        daily_usage[d] += r.get("usage_duration", 0)

    # Sort by date (oldest to newest)
    daily_usage_data = []
    for i in range(6, -1, -1):  # Last 7 days in order
        day_date = (ist_now - timedelta(days=i)).date()
        day_str = day_date.strftime("%d %b")
        daily_usage_data.append({"date": day_str, "usage": daily_usage.get(day_date, 0)})
    # -------- MOST USED APP --------
    app_map = {}

    for r in filtered:
        app = r.get("active_app", "Unknown")
        app_map[app] = app_map.get(app, 0) + r.get("usage_duration", 0)

    most_used_app = max(app_map, key=app_map.get) if app_map else "None"

    # -------- HOURLY --------
    hourly = defaultdict(int)

    for r in filtered:
        h = r["timestamp"].replace(tzinfo=pytz.utc).astimezone(ist).strftime("%H")
        hourly[h] += r.get("usage_duration", 0) 

    hourly_data = [{"hour": h, "usage": v} for h, v in sorted(hourly.items())]

    # -------- WEEKLY --------
    weekly = defaultdict(int)

    for r in filtered:
        d = r["timestamp"].strftime("%a")
        weekly[d] += r.get("usage_duration", 0)

    order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    weekly_data = [
        {"day": d, "usage": weekly.get(d, 0)}
        for d in order
    ]

    # -------- FOCUS --------
    focus = sum(r["usage_duration"] for r in filtered if r.get("app_category")=="HIGH")
    total = sum(r["usage_duration"] for r in filtered)

    focus_ratio = round((focus/total)*100,2) if total else 0

    # ✅ CORRECT VERSION (use your own variable)
    total_usage = sum([d["usage"] for d in daily_usage_data])
    avg_daily = total_usage / 7  # Always average over 7 days
    
    return {
        
        "range": "7 days",
        "avg_daily_usage": round(avg_daily,2),
        "focus_ratio": focus_ratio,
        "most_used_app": most_used_app,
        "hourly": hourly_data,
        "weekly": weekly_data,
        "daily": daily_usage_data,
        "laptop_usage": filtered  # 🔥 Include raw 7-day data for AnalyticsPage
    }