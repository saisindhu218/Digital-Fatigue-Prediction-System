import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from src.config import settings
import json


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

    def get_app_category(self, app, title):
        """
        Dynamically categorize apps based on updated keywords or external configuration.
        """
        name = (app + " " + title).lower()
        high = ["code", "pycharm", "intellij", "studio", "notepad", "sublime"]
        medium = ["word", "excel", "powerpoint", "docs", "reading"]
        low = ["youtube", "netflix", "spotify", "instagram", "facebook", "video"]
        
        # Dynamically load additional categories from a configuration file or API
        try:
            with open("app_categories.json", "r") as f:
                categories = json.load(f)
                high.extend(categories.get("high", []))
                medium.extend(categories.get("medium", []))
                low.extend(categories.get("low", []))
        except Exception as e:
            print("[CATEGORY LOAD ERROR]", e)

        if any(x in name for x in high):
            return "HIGH"
        elif any(x in name for x in medium):
            return "MEDIUM"
        elif any(x in name for x in low):
            return "LOW"
        return "MEDIUM"

    def _smooth_fatigue_score(self, raw_score: float) -> float:
        """
        Keep the output away from hard 0/100 edges so the score changes naturally.
        """
        bounded_score = max(0.0, min(100.0, float(raw_score)))
        return 5.0 + 90.0 * (1.0 / (1.0 + np.exp(-((bounded_score - 50.0) / 10.0))))

    def predict_fatigue(self, features: dict):
        """
        Refined fatigue prediction logic with dynamic adjustments.
        """
        try:
            # Extract features with defaults
            feature_defaults = {
                "screen_time": 0,
                "idle_ratio": 0,
                "switches_per_hour": 0,
                "keystrokes_per_hour": 0,
                "mouse_per_hour": 0,
                "cognitive_load": 2,
                "night_ratio": 0,
                "productive_ratio": 0,
                "fatigue_break_bonus": 0,
                "fatigue_session_penalty": 0
            }
            extracted_features = {key: features.get(key, default) for key, default in feature_defaults.items()}

            # Mouse-move counts can be extremely large on desktop systems.
            # Cap them before scoring so the behavioral score does not collapse to 0.
            keystrokes_per_hour = min(float(extracted_features["keystrokes_per_hour"]), 600.0)
            mouse_per_hour = min(float(extracted_features["mouse_per_hour"]), 1200.0)
            switches_per_hour = min(float(extracted_features["switches_per_hour"]), 180.0)
            screen_time = min(float(extracted_features["screen_time"]), 16.0)
            idle_ratio = min(max(float(extracted_features["idle_ratio"]), 0.0), 1.0)
            productive_ratio = min(max(float(extracted_features["productive_ratio"]), 0.0), 1.0)
            night_ratio = min(max(float(extracted_features["night_ratio"]), 0.0), 1.0)
            cognitive_load = min(max(float(extracted_features["cognitive_load"]), 0.0), 10.0)
            fatigue_break_bonus = max(float(extracted_features["fatigue_break_bonus"]), -40.0)
            fatigue_session_penalty = min(max(float(extracted_features["fatigue_session_penalty"]), 0.0), 40.0)

            # Convert the raw conditions into a smoother 0-100 fatigue pressure score.
            activity_pressure = (
                min(screen_time / 16.0, 1.0) * 18.0 +
                idle_ratio * 24.0 +
                min(switches_per_hour / 60.0, 1.0) * 14.0 +
                (cognitive_load / 10.0) * 16.0 +
                night_ratio * 14.0 +
                min(keystrokes_per_hour / 250.0, 1.0) * 6.0 +
                min(mouse_per_hour / 500.0, 1.0) * 4.0 +
                min(fatigue_session_penalty / 8.0, 5.0)
            )

            recovery = (
                productive_ratio * 22.0 +
                min(max(-fatigue_break_bonus, 0.0) / 8.0, 5.0) * 1.5
            )

            behavioral_score = 35.0 + activity_pressure - recovery
            behavioral_score = max(0.0, min(100.0, behavioral_score))
            smooth_score = self._smooth_fatigue_score(behavioral_score)

            if self.is_loaded:
                X = pd.DataFrame([{
                    "screen_time": screen_time,
                    "avg_session": features.get("avg_session", 0),
                    "breaks": features.get("breaks", 0),
                    "night_ratio": night_ratio,
                    "productive_ratio": productive_ratio
                }])

                pred = self.fatigue_classifier.predict(X)[0]
                label = self.fatigue_label_encoder.inverse_transform([pred])[0]

                confidence = (
                    float(max(self.fatigue_classifier.predict_proba(X)[0]))
                    if hasattr(self.fatigue_classifier, "predict_proba")
                    else 0.85
                )

                score = smooth_score * {
                    "Low": 0.5,
                    "Medium": 0.8
                }.get(label, 1)

            else:
                score = smooth_score
                confidence = 0.82
                label = (
                    "Low" if score < 35 else
                    "Medium" if score < 65 else
                    "High"
                )

            return {
                "level": label,
                "score": round(float(score), 2),
                "confidence": confidence
            }

        except KeyError as e:
            print("⚠️ Missing feature key:", e)
        except Exception as e:
            print("⚠️ Fatigue prediction error:", e)
            return {
                "level": "Medium",
                "score": 50,
                "confidence": 0.7
            }

    # ---------------- PRODUCTIVITY LOSS ----------------

    def predict_productivity_loss(self, features: dict, fatigue_score=None):
        """
        Estimate productivity loss in hours per day.
        Recalibrated for 10-min windows:
        - Factor in actual work quality (focus score, app context)
        - Reduce penalty for engaged productive sessions
        - Weight context switching impact by whether user is in flow
        """
        try:

            screen = features.get("screen_time", 0)
            productive = features.get("productive_ratio", 0.5)
            focus = features.get("focus_score", 50)
            switches = features.get("switches_per_hour", 0)
            cognitive = features.get("cognitive_load", 2)

            if fatigue_score is None:
                fatigue_score = self.predict_fatigue(features)["score"]

            # Context: is user in engaged productive work?
            in_flow = productive > 0.65 and focus > 65 and switches < 15

            # RECALIBRATED behavioral loss for 10-min windows
            # Lower base values since we're measuring shorter periods
            behavioral_loss = (
                screen * 0.10 +      # Screen exposure penalty (reduced from 0.15)
                fatigue_score * 0.025 +  # Fatigue impact (reduced from 0.03)
                (1 - productive) * 2.5 + # Unproductive time cost (reduced from 3)
                (100 - focus) * 0.015    # Low focus penalty (reduced from 0.02)
            )

            # If in flow state, reduce context-switching penalty significantly
            if not in_flow:
                behavioral_loss += switches * 0.08  # Extra penalty for excessive switching outside flow

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
        """
        Calculate overall productivity score (0-100).
        Recalibrated for 10-min windows:
        - Emphasize QUALITY over quantity
        - High productive ratio + focus = excellent productivity
        - Even with fatigue, engaged work shows good productivity
        """
        try:

            # Recalibrated weights for shorter windows
            # More emphasis on quality indicators (focus, productive work)
            # Less raw emphasis on fatigue in isolation
            score = (
                productive_ratio * 50 +   # Quality of work matters most (reduced from 60)
                focus_score * 0.4 +       # Focus state important (increased from 0.3)
                (100 - fatigue_score) * 0.35  # Fatigue inverse (reduced from 0.4)
            )

            return round(max(0, min(100, score)), 2)

        except:
            return 65.0

    # ---------------- CONFIDENCE ESTIMATION ----------------

    def estimate_confidence(self, sample_count: int) -> float:

        try:

            if sample_count <= 0:
                return 0.0

            confidence = min(100, round(sample_count * 5))

            return float(confidence)

        except:
            return 0.0

    def estimate_productivity_confidence(
        self,
        sample_count: int,
        productive_ratio: float = 0.5,
        focus_score: float = 50,
        productivity_loss: float = 0,
    ) -> float:

        try:

            if sample_count <= 0:
                return 0.0

            data_confidence = min(55, sample_count * 3)
            signal_confidence = min(30, abs(productive_ratio - 0.5) * 60)
            focus_confidence = min(15, abs(focus_score - 50) * 0.3)
            loss_confidence = min(15, productivity_loss * 2)

            confidence = data_confidence + signal_confidence + focus_confidence + loss_confidence

            return float(min(100, round(confidence)))

        except:
            return 0.0


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
                "description": f"Fatigue is currently high ({fatigue_score:.0f}%). Take a 10-15 minute break away from the screen."
            })

        if fatigue_score > 70:
            recommendations.append({
                "type": "health",
                "title": "Reduce screen exposure",
                "description": f"High fatigue score detected ({fatigue_score:.0f}%). Try reducing continuous screen exposure now."
            })

        if screen > 6:
            recommendations.append({
                "type": "screen",
                "title": "Limit long screen sessions",
                "description": f"Screen time is {screen:.1f}h today. Add short breaks every hour to prevent fatigue buildup."
            })

        if switches > 20:
            recommendations.append({
                "type": "focus",
                "title": "Reduce context switching",
                "description": f"Frequent app switching detected ({switches:.1f}/hour). Batch similar tasks to improve focus continuity."
            })

        if idle > 0.25:
            recommendations.append({
                "type": "productivity",
                "title": "Reduce idle distractions",
                "description": f"Idle ratio is {idle * 100:.0f}%. Use focus timers or block distracting apps during deep work blocks."
            })

        if night > 0.4:
            recommendations.append({
                "type": "sleep",
                "title": "Avoid late-night usage",
                "description": f"Late-night usage ratio is {night * 100:.0f}%. Reducing night sessions can improve next-day energy."
            })

        if productivity_loss > 3:
            recommendations.append({
                "type": "productivity",
                "title": "Improve focus sessions",
                "description": f"Estimated productivity loss is {productivity_loss:.1f}h/week. Try 25-minute focus sessions with planned breaks."
            })

        if productive > 0.7 and focus > 70:
            recommendations.append({
                "type": "positive",
                "title": "Great focus today",
                "description": f"Strong pattern detected (productive ratio {productive * 100:.0f}%, focus {focus:.0f}). Keep this balanced routine."
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