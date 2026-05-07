import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from typing import Any
try:
    from pymongo.errors import PyMongoError
except Exception:
    # If pymongo isn't importable in some environments, fall back to Exception
    PyMongoError = Exception
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


API_PREFIX = "/api/v1"
APP_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("BACKEND_PORT", "8000"))


# ---------------- LIFESPAN EVENTS ----------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("\n🚀 Starting Digital Fatigue Guard Backend")

    # -------- DATABASE --------
    try:
        from src.database import db
        await db.connect()
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

    # -------- ML MODELS --------
    try:
        from src.services.ml_service import ml_service
        if not ml_service.is_loaded:
            ml_service.load_models()

        if ml_service.is_loaded:
            print("✅ ML models ready")
        else:
            print("⚠️ ML models not available (fallback mode)")

    except Exception as e:
        print(f"⚠️ ML model initialization failed: {e}")

    yield

    # -------- SHUTDOWN --------
    try:
        from src.database import db
        db.disconnect()
        print("🔌 Database disconnected")
    except Exception as e:
        print(f"⚠️ Database disconnect warning: {e}")

    print("🛑 Backend shutdown complete\n")


# ---------------- CREATE FASTAPI APP ----------------

app = FastAPI(
    title="Digital Fatigue Guard",
    description="AI-Based Digital Fatigue & Productivity Prediction API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# ---------------- CORS CONFIG ----------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- ROUTERS ----------------

from src.routes.auth import router as auth_router
from src.routes.pairing import router as pairing_router
from src.routes.usage import router as usage_router
from src.routes.prediction import router as prediction_router
from src.routes.preferences import router as preferences_router
from src.routes.debug import router as debug_router

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(pairing_router, prefix=API_PREFIX)
app.include_router(usage_router, prefix=API_PREFIX)
app.include_router(prediction_router, prefix=API_PREFIX)
app.include_router(preferences_router, prefix=API_PREFIX)
app.include_router(debug_router, prefix=API_PREFIX)

print("✅ Routers loaded: auth, pairing, usage, prediction, preferences, debug")


# ---------------- GLOBAL EXCEPTION HANDLERS ----------------
@app.exception_handler(PyMongoError)
async def pymongo_exception_handler(request: Any, exc: PyMongoError):
    # Return a concise, user-friendly error when database/network issues occur
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Database temporarily unavailable. Please check your network or try again later."
        },
    )


# ---------------- BASIC ROUTES ----------------

@app.get("/")
async def root():
    return {
        "message": "Digital Fatigue Guard API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():

    try:
        from src.database import db
        db_status = "connected" if db.client else "disconnected"
    except Exception:
        db_status = "unknown"

    try:
        from src.services.ml_service import ml_service
        ml_status = "loaded" if ml_service.is_loaded else "fallback"
    except Exception:
        ml_status = "unknown"

    return {
        "status": "running",
        "database": db_status,
        "ml_models": ml_status,
        "environment": "development"
    }


@app.get("/config")
async def show_config():

    from src.config import settings

    mongodb_url = settings.MONGODB_URL

    if "@" in mongodb_url:
        parts = mongodb_url.split("@")
        mongodb_url = f"mongodb://***:***@{parts[1]}"

    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database_name": settings.DATABASE_NAME,
        "mongodb_url": mongodb_url,
        "jwt_algorithm": settings.ALGORITHM,
        "token_expiry_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES
    }


# ---------------- RUN SERVER ----------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        log_level="info"
    )