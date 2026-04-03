from fastapi import APIRouter
from datetime import datetime, timedelta, timezone
from src.database import db
from src.services.feature_extractor import LiveFeatureExtractor
from src.services.ml_service import ml_service
import uuid
import pytz
router = APIRouter(prefix="/usage", tags=["usage"])

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

    now = datetime.utcnow()

    # find last prediction time
    last_prediction = await db.db.predictions.find_one(
        {"user_id": user_id},
        sort=[("timestamp", -1)]
    )

#    if last_prediction:
#        last_time = last_prediction["timestamp"]
 #   else:
  #      last_time = now - timedelta(minutes=10)

    # 👉 take ONLY data after last prediction
   # cutoff = last_time

    cutoff = datetime.utcnow() - timedelta(minutes=10)

    laptop_data = await db.db.usage_data.find({
        "user_id": user_id,
        "data_type": "laptop",
        "timestamp": {"$gte": cutoff}
    }).sort("timestamp", -1).limit(500).to_list(500)
    
    mobile_data = await db.db.usage_data.find({
        "user_id": user_id,
        "data_type": "mobile",
        "timestamp": {"$gte": cutoff}
    }).sort("timestamp", -1).limit(500).to_list(500)

    features = feature_extractor.extract_features_from_live_data(
        laptop_data,
        mobile_data,
        user_id
    )

    fatigue_result = ml_service.predict_fatigue(features)

    productivity_loss = ml_service.predict_productivity_loss(features)

    productivity_score = max(0, 100 - productivity_loss * 5)

    prediction_record = {
        "_id": str(uuid.uuid4()),
        "user_id": user_id,
        "timestamp": datetime.utcnow(),
        "fatigue_level": fatigue_result["level"],
        "fatigue_score": fatigue_result["score"],
        "confidence": fatigue_result["confidence"],
        "productivity_loss_hours": productivity_loss,
        "productivity_score": productivity_score
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
    
    if not laptop_data and not mobile_data:
        print("⚠️ No data for prediction")
        return
    
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

        productivity = {
            "productivity_score": p.get("productivity_score"),
            "productivity_loss_hours": p.get("productivity_loss_hours"),
            "breakdown": {
                "Fatigue": fatigue_hours,
                "Context Switching": context_hours,
                "Distractions": distraction_hours
            }
        }

        features = feature_extractor.extract_features_from_live_data(
            laptop,
            mobile,
            user_id
        )

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
async def get_trends(user_id: str, days: int = 7):

    cutoff = datetime.utcnow() - timedelta(days=days)

    preds = await db.db.predictions.find({
        "user_id": user_id,
        "timestamp": {"$gte": cutoff}
    }).sort("timestamp", 1).to_list(200)

    fatigue_trend = []
    productivity_trend = []

    if not preds:
        return {
            "fatigueTrend": [],
            "productivityTrend": []
        }

    # check how many unique days exist
    unique_days = list(set(
        p["timestamp"].replace(tzinfo=pytz.utc).astimezone(ist).strftime("%Y-%m-%d")
        for p in preds
    ))

    # -------- CASE 1: ONLY ONE DAY (TODAY) --------
    if len(unique_days) == 1:

        time_groups = {}

        for p in preds:
            local_time = p["timestamp"].replace(tzinfo=pytz.utc).astimezone(ist)
            time_label = local_time.strftime("%H:%M")
            
            if time_label not in time_groups:
                time_groups[time_label] = {"fatigue": [], "productivity": []}

            time_groups[time_label]["fatigue"].append(p.get("fatigue_score", 0))
            time_groups[time_label]["productivity"].append(p.get("productivity_score", 0))


        for time_label, values in time_groups.items():

            fatigue_trend.append({
                "day": time_label,
                "score": round(sum(values["fatigue"]) / len(values["fatigue"]), 2)
            })

            productivity_trend.append({
                "day": time_label,
                "score": round(sum(values["productivity"]) / len(values["productivity"]), 2)
            })
    # -------- CASE 2: MULTIPLE DAYS --------
    else:

        daily = {}

        for p in preds:
            local_time = p["timestamp"].replace(tzinfo=pytz.utc).astimezone(ist)
            day = local_time.strftime("%Y-%m-%d")

            if day not in daily:
                daily[day] = {"fatigue": [], "productivity": []}

            daily[day]["fatigue"].append(p.get("fatigue_score", 0))
            daily[day]["productivity"].append(p.get("productivity_score", 0))

        today = datetime.now(ist).date()   # ✅ ONLY DATE (important)

       # order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        # generate all last N days
        all_days = [
            (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
             for i in range(days-1, -1, -1)
        ]

        for day in all_days:
            if day in daily:
                values = daily[day]

                fatigue_trend.append({
                    "day": day,
                    "score": values["fatigue"][-1] #round(sum(values["fatigue"]) / len(values["fatigue"]), 2)
                })

                productivity_trend.append({
                    "day": day,
                    "score": values["productivity"][-1] # round(sum(values["productivity"]) / len(values["productivity"]), 2)
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
    
    cutoff = datetime.utcnow() - timedelta(days=7)

    records = await db.db.usage_data.find({
        "user_id": user_id,
        "data_type": "laptop",
        "timestamp": {"$gte": cutoff}
    }).to_list(2000)
    
    if not records:
        return {}

    # -------- DYNAMIC RANGE --------
    days = list(set(r["timestamp"].strftime("%Y-%m-%d") for r in records))
    total_days = len(days)

    if total_days >= 30:
        days_to_use = 30
    elif total_days >= 7:
        days_to_use = 7
    else:
        days_to_use = total_days

    cutoff = datetime.utcnow() - timedelta(days=days_to_use)

    filtered = [r for r in records if r["timestamp"] >= cutoff]

    # -------- AVG DAILY --------
    from collections import defaultdict

    daily_usage = defaultdict(int)

    for r in filtered:
        d = r["timestamp"].replace(tzinfo=pytz.utc).astimezone(ist).strftime("%d %b")
        daily_usage[d] += r.get("usage_duration", 0)

    daily_usage_data = [
        {"date": d, "usage": v}
        for d, v in sorted(daily_usage.items())
    ]
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
    days = len(daily_usage_data) if daily_usage_data else 1
    avg_daily = total_usage / days
    
    return {
        
        "range": f"{days_to_use} days",
        "avg_daily_usage": round(avg_daily,2),
        "focus_ratio": focus_ratio,
        "most_used_app": most_used_app,
        "hourly": hourly_data,
        "weekly": weekly_data,
        "daily": daily_usage_data
    }