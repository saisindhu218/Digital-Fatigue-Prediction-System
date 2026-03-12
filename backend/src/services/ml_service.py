import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from src.config import settings


class MLService:

    def __init__(self):

        self.fatigue_classifier = None
        self.fatigue_label_encoder = None
        self.productivity_model = None

        self.is_loaded = False
        self.models_dir = Path(settings.ML_MODELS_DIR)

    # ---------------- LOAD MODELS ----------------

    def load_models(self):

        try:

            if not self.models_dir.exists():
                print("⚠️ ML models directory not found")
                self.is_loaded = False
                return

            classifier = self.models_dir / "fatigue_classifier.pkl"
            encoder = self.models_dir / "fatigue_label_encoder.pkl"
            productivity = self.models_dir / "productivity_loss_model.pkl"

            if classifier.exists():
                self.fatigue_classifier = joblib.load(classifier)

            if encoder.exists():
                self.fatigue_label_encoder = joblib.load(encoder)

            if productivity.exists():
                self.productivity_model = joblib.load(productivity)

            self.is_loaded = (
                self.fatigue_classifier is not None and
                self.fatigue_label_encoder is not None and
                self.productivity_model is not None
            )

            if self.is_loaded:
                print("✅ ML models loaded successfully")
            else:
                print("⚠️ Using behavioral prediction fallback")

        except Exception as e:

            print("❌ Model load error:", e)
            self.is_loaded = False

    # ---------------- FATIGUE PREDICTION ----------------

    def predict_fatigue(self, features: dict):

        try:

            screen = features.get("screen_time", 0)
            idle = features.get("idle_ratio", 0)
            switches = features.get("switches_per_hour", 0)
            keys = features.get("keystrokes_per_hour", 0)
            mouse = features.get("mouse_per_hour", 0)
            cognitive = features.get("cognitive_load", 2)
            night = features.get("night_ratio", 0)
            productive = features.get("productive_ratio", 0)

            behavioral_score = (
                screen * 12 +
                idle * 40 +
                switches * 1.5 +
                cognitive * 8 +
                night * 25 -
                productive * 20 -
                keys * 0.01 -
                mouse * 0.005
            )

            behavioral_score = max(0, min(100, behavioral_score))

            if self.is_loaded:

                X = pd.DataFrame([{
                    "screen_time": features.get("screen_time", 0),
                    "avg_session": features.get("avg_session", 0),
                    "breaks": features.get("breaks", 0),
                    "night_ratio": features.get("night_ratio", 0),
                    "productive_ratio": features.get("productive_ratio", 0)
                }])

                pred = self.fatigue_classifier.predict(X)[0]
                label = self.fatigue_label_encoder.inverse_transform([pred])[0]

                if hasattr(self.fatigue_classifier, "predict_proba"):
                    confidence = float(
                        max(self.fatigue_classifier.predict_proba(X)[0])
                    )
                else:
                    confidence = 0.85

                if label == "Low":
                    score = behavioral_score * 0.5
                elif label == "Medium":
                    score = behavioral_score * 0.8
                else:
                    score = behavioral_score

            else:

                score = behavioral_score
                confidence = 0.82

                if score < 35:
                    label = "Low"
                elif score < 65:
                    label = "Medium"
                else:
                    label = "High"

            return {
                "level": label,
                "score": round(float(score), 2),
                "confidence": confidence
            }

        except Exception as e:

            print("⚠️ Fatigue prediction error:", e)

            return {
                "level": "Medium",
                "score": 50,
                "confidence": 0.7
            }

    # ---------------- PRODUCTIVITY LOSS ----------------

    def predict_productivity_loss(self, features: dict, fatigue_score=None):

        try:

            screen = features.get("screen_time", 0)
            productive = features.get("productive_ratio", 0.5)
            focus = features.get("focus_score", 50)

            if fatigue_score is None:
                fatigue_score = self.predict_fatigue(features)["score"]

            behavioral_loss = (
                screen * 0.15 +
                fatigue_score * 0.03 +
                (1 - productive) * 3 +
                (100 - focus) * 0.02
            )

            behavioral_loss = max(0, min(8, behavioral_loss))

            if self.is_loaded:

                X = pd.DataFrame([{
                    "screen_time": features.get("screen_time", 0),
                    "avg_session": features.get("avg_session", 0),
                    "breaks": features.get("breaks", 0),
                    "night_ratio": features.get("night_ratio", 0),
                    "productive_ratio": features.get("productive_ratio", 0),
                    "fatigue_score": fatigue_score
                }])

                loss = float(self.productivity_model.predict(X)[0])

            else:

                loss = behavioral_loss

            return round(float(loss), 2)

        except Exception as e:

            print("⚠️ Productivity prediction error:", e)

            return 2.0

    # ---------------- PRODUCTIVITY SCORE ----------------

    def calculate_productivity_score(self, fatigue_score, productive_ratio, focus_score):

        try:

            score = (
                productive_ratio * 60 +
                focus_score * 0.3 +
                (100 - fatigue_score) * 0.4
            )

            return round(max(0, min(100, score)), 2)

        except:
            return 65.0


    # ---------------- RECOMMENDATIONS ----------------

    def generate_recommendations(self, features: dict, fatigue_result: dict, productivity_loss: float):

        recommendations = []

        screen = features.get("screen_time", 0)
        idle = features.get("idle_ratio", 0)
        switches = features.get("switches_per_hour", 0)
        night = features.get("night_ratio", 0)
        productive = features.get("productive_ratio", 0)
        focus = features.get("focus_score", 50)

        fatigue_level = fatigue_result.get("level", "Medium")
        fatigue_score = fatigue_result.get("score", 50)

        if fatigue_level == "High":
            recommendations.append({
                "type": "fatigue",
                "title": "Take a break",
                "description": "Your fatigue level is high. Take a 10-15 minute break away from the screen."
            })

        if fatigue_score > 70:
            recommendations.append({
                "type": "health",
                "title": "Reduce screen exposure",
                "description": "High fatigue score detected. Try reducing continuous screen time."
            })

        if screen > 6:
            recommendations.append({
                "type": "screen",
                "title": "Limit long screen sessions",
                "description": "Your screen time is high today. Consider adding short breaks every hour."
            })

        if switches > 20:
            recommendations.append({
                "type": "focus",
                "title": "Reduce context switching",
                "description": "Frequent app switching detected. Try batching similar tasks together."
            })

        if idle > 0.25:
            recommendations.append({
                "type": "productivity",
                "title": "Reduce idle distractions",
                "description": "High idle time detected. Consider using focus timers or blocking distracting apps."
            })

        if night > 0.4:
            recommendations.append({
                "type": "sleep",
                "title": "Avoid late-night usage",
                "description": "Late-night screen activity may increase fatigue and reduce productivity."
            })

        if productivity_loss > 3:
            recommendations.append({
                "type": "productivity",
                "title": "Improve focus sessions",
                "description": "Your productivity loss is high today. Try 25-minute focus sessions with breaks."
            })

        if productive > 0.7 and focus > 70:
            recommendations.append({
                "type": "positive",
                "title": "Great focus today",
                "description": "Your productivity patterns look healthy. Keep maintaining balanced work sessions."
            })

        if not recommendations:
            recommendations.append({
                "type": "general",
                "title": "Maintain healthy habits",
                "description": "Your digital usage patterns look balanced. Continue maintaining good work habits."
            })

        return recommendations


# GLOBAL INSTANCE
ml_service = MLService()
ml_service.load_models()