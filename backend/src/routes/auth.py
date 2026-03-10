from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from src.config import settings
from src.models.user import UserCreate, UserInDB, Token, UserLogin
from src.database import db
import uuid

router = APIRouter(prefix="/auth", tags=["authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ================= PASSWORD FUNCTIONS =================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password safely (bcrypt supports max 72 bytes)
    """
    plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password safely (truncate to 72 bytes for bcrypt)
    """
    password = password[:72]
    return pwd_context.hash(password)


# ================= TOKEN CREATION =================

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )


# ================= REGISTER =================

@router.post("/register", response_model=UserInDB, status_code=201)
async def register(user_data: UserCreate):
    """Register a new user"""

    if db.db is None:
        raise HTTPException(
            status_code=503,
            detail="Database connection not available"
        )

    try:
        email = user_data.email.lower().strip()

        # Check if user exists
        existing = await db.db.users.find_one({"email": email})
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        user_id = str(uuid.uuid4())

        hashed_password = get_password_hash(user_data.password)

        user = {
            "_id": user_id,
            "email": email,
            "full_name": user_data.full_name.strip(),
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
            "is_active": True,
            "devices": []
        }

        await db.db.users.insert_one(user)

        return UserInDB(
            id=user_id,
            email=email,
            full_name=user_data.full_name,
            created_at=user["created_at"],
            is_active=True,
            devices=[]
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )


# ================= LOGIN =================

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):

    if db.db is None:
        raise HTTPException(
            status_code=503,
            detail="Database not connected"
        )

    try:
        email = user_data.email.lower().strip()
        password = user_data.password[:72]

        if not email or not password:
            raise HTTPException(
                status_code=400,
                detail="Email and password required"
            )

        user = await db.db.users.find_one({"email": email})

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        if not verify_password(password, user["hashed_password"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        token = create_access_token({
            "sub": email,
            "user_id": user["_id"]
        })

        return Token(
            access_token=token,
            token_type="bearer"
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {str(e)}"
        )


# ================= DEBUG =================

@router.get("/debug")
async def debug_users():
    """List all users (debug only)"""

    if db.db is None:
        return {"error": "Database not connected"}

    try:
        users = []

        cursor = db.db.users.find({}, {"hashed_password": 0})

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            users.append(doc)

        total = await db.db.users.count_documents({})

        return {
            "connected": True,
            "total_users": total,
            "users": users,
            "database": settings.DATABASE_NAME
        }

    except Exception as e:
        return {"error": str(e)}