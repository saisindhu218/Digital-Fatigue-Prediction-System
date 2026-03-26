from fastapi import APIRouter, HTTPException, status, Request
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.config import settings
from src.models.user import UserCreate, UserInDB, Token, UserLogin
from src.database import db
import uuid

router = APIRouter(prefix="/auth", tags=["authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ========== REGISTER ==========
@router.post("/register", response_model=UserInDB, status_code=201)
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
            "created_at": datetime.utcnow(),
            "is_active": True,
            "devices": []
        }
        
        # Insert into database
        result = await db.db.users.insert_one(user)
        print(f"✅ Inserted with ID: {result.inserted_id}")
        
        # Verify it was saved
        saved = await db.db.users.find_one({"_id": user_id})
        if saved:
            print(f"✅ Verified user in database: {email}")
        else:
            print(f"❌ Failed to verify user in database")
            raise HTTPException(status_code=500, detail="Failed to save user")
        
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
        print(f"✅ Login successful: {email}")

        # Save active user locally for collectors
       # Save active user info for collectors
        try:
            with open("active_user.txt", "w") as f:
             f.write(f"{user['full_name']}|{user['_id']}")
        except Exception as e:
         print("Failed to write active user:", e)

        return Token(access_token=token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

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