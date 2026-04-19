from fastapi import APIRouter, HTTPException, status, Request, Depends
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from src.config import settings
from src.models.user import UserCreate, UserInDB, Token, UserLogin, TokenData, RefreshTokenRequest
from src.database import db
import uuid

router = APIRouter(prefix="/auth", tags=["authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
REFRESH_TOKEN_EXPIRE_DAYS = int(getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", 30))
DATABASE_NOT_CONNECTED = "Database not connected"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    if expires_delta is None and settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = data.copy()
    to_encode["token_use"] = ACCESS_TOKEN_TYPE
    if expires_delta:
        expire = _utc_now() + expires_delta
        to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict):
    expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode["token_use"] = REFRESH_TOKEN_TYPE
    expire = _utc_now() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Validate JWT token and return current user identity."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str | None = payload.get("sub")
        user_id: str | None = payload.get("user_id")
        token_use: str | None = payload.get("token_use")
        if email is None or user_id is None or token_use != ACCESS_TOKEN_TYPE:
            raise credentials_exception
        token_data = TokenData(email=email, user_id=user_id)
    except JWTError:
        raise credentials_exception

    if db.db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=DATABASE_NOT_CONNECTED)

    user = await db.db.users.find_one({"_id": token_data.user_id})
    if user is None:
        raise credentials_exception

    return {"email": token_data.email, "user_id": token_data.user_id}


# ========== REGISTER ==========
@router.post("/register", response_model=Token, status_code=201)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check database connection
    if db.db is None:
        print("❌ Database not connected")
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        email = user_data.email.lower().strip()
        print(f"📝 Registering: {email}")
        
        # Check if user exists
        existing = await db.db.users.find_one({"email": email})
        if existing:
            print(f"❌ Email already exists: {email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user_id = str(uuid.uuid4())
        hashed = get_password_hash(user_data.password)
        
        user = {
            "_id": user_id,
            "email": email,
            "full_name": user_data.full_name.strip(),
            "hashed_password": hashed,
            "created_at": _utc_now(),
            "is_active": True,
            "devices": [],
            "preferences": {
                "break_alerts": True,
                "fatigue_alerts": True,
                "weekly_digest": False
            },
            "goals": {
                "target_focus_score": 80,
                "max_fatigue_threshold": 75,
                "daily_screen_limit_hours": 8.0,
                "preferred_work_slot": "09:00-17:00"
            },
            "notifications": []
        }
        
        # Insert into database
        result = await db.db.users.insert_one(user)
        print(f"✅ Inserted with ID: {result.inserted_id}")
        
        # Verify it was saved
        saved = await db.db.users.find_one({"_id": user_id})
        if saved:
            print(f"✅ Verified user in database: {email}")
        else:
            print("❌ Failed to verify user in database")
            raise HTTPException(status_code=500, detail="Failed to save user")
        
        token = create_access_token({"sub": email, "user_id": user_id})
        refresh_token = create_refresh_token({"sub": email, "user_id": user_id})

        return Token(access_token=token, token_type="bearer", user_id=user_id, refresh_token=refresh_token)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


# ========== LOGIN ==========
@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):

    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    try:
        email = user_data.email.lower().strip()
        password = user_data.password

        print(f"🔐 Login attempt: {email}")

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")

        # Find user
        user = await db.db.users.find_one({"email": email})
        if not user:
            print(f"❌ User not found: {email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Verify password
        if not verify_password(password, user["hashed_password"]):
            print(f"❌ Wrong password for: {email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Create token
        token = create_access_token({"sub": email, "user_id": user["_id"]})
        refresh_token = create_refresh_token({"sub": email, "user_id": user["_id"]})
        print(f"✅ Login successful: {email}")

        # Save active user locally for collectors
       # Save active user info for collectors
        try:
            with open("active_user.txt", "w") as f:
             f.write(f"{user['full_name']}|{user['_id']}")
        except Exception as e:
         print("Failed to write active user:", e)

        return Token(access_token=token, token_type="bearer", user_id=user["_id"], refresh_token=refresh_token)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/refresh", response_model=Token)
async def refresh_token(payload: RefreshTokenRequest):
    if db.db is None:
        raise HTTPException(status_code=503, detail=DATABASE_NOT_CONNECTED)

    try:
        token_payload = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if token_payload.get("token_use") != REFRESH_TOKEN_TYPE:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        email: str | None = token_payload.get("sub")
        user_id: str | None = token_payload.get("user_id")
        if email is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = await db.db.users.find_one({"_id": user_id})
        if user is None or user.get("email") != email:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        access_token = create_access_token({"sub": email, "user_id": user_id})
        new_refresh_token = create_refresh_token({"sub": email, "user_id": user_id})

        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user_id,
            refresh_token=new_refresh_token,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

# ========== DEBUG - Check users ==========
@router.get("/debug")
async def debug_users():
    """List all users (debug only)"""
    if db.db is None:
        return {"error": "Database not connected"}
    
    try:
        # Get all users
        users = []
        cursor = db.db.users.find({}, {"hashed_password": 0})
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            users.append(doc)
        
        # Count total
        total = await db.db.users.count_documents({})
        
        return {
            "connected": True,
            "total_users": total,
            "users": users,
            "database": settings.DATABASE_NAME
        }
    except Exception as e:
        return {"error": str(e)}