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
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # QR Codes
    QR_CODE_EXPIRY_MINUTES = int(os.getenv("QR_CODE_EXPIRY_MINUTES", "5"))
    
    # Thresholds
    FATIGUE_HIGH_THRESHOLD = int(os.getenv("FATIGUE_HIGH_THRESHOLD", "70"))
    PRODUCTIVITY_LOSS_THRESHOLD = int(os.getenv("PRODUCTIVITY_LOSS_THRESHOLD", "10"))
    
    # ML Models
    ML_MODELS_DIR = os.getenv("ML_MODELS_DIR", str(BASE_DIR / "ml_models"))


settings = Settings()

# ADD THESE DEBUG LINES
print(f"🔧 Config loaded:")
print(f"   MongoDB URL: {settings.MONGODB_URL.split('@')[0]}@***")
print(f"   Database: {settings.DATABASE_NAME}")
print(f"   JWT Algorithm: {settings.ALGORITHM}")
print(f"   Token expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")