import os
from pathlib import Path
from dotenv import load_dotenv

# ===== FORCE LOAD .env FROM BACKEND ROOT =====
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    # Application
    PROJECT_NAME = "Digital Fatigue Guard"
    VERSION = "1.0.0"
    API_V1_STR = "/api/v1"
    
    # MongoDB
    MONGODB_URL = os.getenv("MONGODB_URL")
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    
    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "20"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # QR Codes
    QR_CODE_EXPIRY_MINUTES = int(os.getenv("QR_CODE_EXPIRY_MINUTES", "5"))
    
    # Thresholds
    FATIGUE_HIGH_THRESHOLD = int(os.getenv("FATIGUE_HIGH_THRESHOLD", "70"))
    PRODUCTIVITY_LOSS_THRESHOLD = int(os.getenv("PRODUCTIVITY_LOSS_THRESHOLD", "10"))
    
    # Public URL of THIS backend, as reachable from a phone scanning a QR
    # code -- e.g. https://your-service.onrender.com in production. Left
    # empty for local dev, where the QR service falls back to detecting
    # the machine's LAN IP (so a phone on the same WiFi can reach it).
    # Getting this wrong means QR pairing silently encodes an
    # unreachable address -- always set this explicitly when deployed.
    BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "").strip().rstrip("/")

    # ML Models
    ML_MODELS_DIR = os.getenv("ML_MODELS_DIR", str(BASE_DIR / "ml_models"))

    # Debug/diagnostic endpoints (list-all-users, raw diagnostics) are OFF
    # by default because they have no authentication -- anyone with the
    # URL could otherwise see every user's email and activity data. Only
    # enable this locally, never on a public Render deployment.
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").strip().lower() == "true"

    # Data retention: the dashboard never looks back further than 7 days
    # (see usage.py's trends/analytics endpoints), so raw activity records
    # and predictions older than this are auto-deleted via a MongoDB TTL
    # index -- keeps the database from growing forever with heartbeat/
    # upload records nobody queries anymore. Set generously above 7 to
    # leave a safety margin for IST/UTC day-boundary edge cases.
    USAGE_DATA_RETENTION_DAYS = int(os.getenv("USAGE_DATA_RETENTION_DAYS", "10"))
    PREDICTIONS_RETENTION_DAYS = int(os.getenv("PREDICTIONS_RETENTION_DAYS", "10"))


settings = Settings()

# ADD THESE DEBUG LINES
print("🔧 Config loaded:")
def _masked_mongodb_url(url: str) -> str:
    """Never print credentials to logs. 'mongodb+srv://user:pass@host/db'
    -> 'mongodb+srv://***:***@host/db'. Render (and most hosts) retain
    startup logs indefinitely, so this used to leak the real DB password
    into plaintext logs on every single boot."""
    if not url or "@" not in url:
        return url
    scheme_and_creds, rest = url.split("@", 1)
    scheme = scheme_and_creds.split("://", 1)[0] if "://" in scheme_and_creds else "mongodb"
    return f"{scheme}://***:***@{rest}"


print(f"   MongoDB URL: {_masked_mongodb_url(settings.MONGODB_URL)}")
print(f"   Database: {settings.DATABASE_NAME}")
print(f"   JWT Algorithm: {settings.ALGORITHM}")
print(f"   Access token expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
print(f"   Refresh token expiry: {settings.REFRESH_TOKEN_EXPIRE_DAYS} days")