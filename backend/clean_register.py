#!/usr/bin/env python3
"""
Clean registration script - NO hardcoded emails
"""
import asyncio
import sys
from pathlib import Path

# Add path
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(BASE_DIR))

async def register_user():
    try:
        from src.database import db
        from src.models.user import UserCreate
        from src.routes.auth import get_password_hash
        import uuid
        from datetime import datetime
        
        # Connect to database
        await db.connect()
        
        if db.db is None:
            print("❌ Database not connected!")
            return
        
        # === CHANGE THIS TO YOUR EMAIL ===
        email = "sindhu@gmail.com"  # ← CHANGE THIS TO YOUR ACTUAL EMAIL
        password = "password123"     # ← CHANGE THIS TO YOUR PASSWORD
        full_name = "Sindhu"         # ← CHANGE THIS TO YOUR NAME
        
        print(f"\n📝 Registering: {email}")
        
        # Check if exists
        existing = await db.db.users.find_one({"email": email})
        if existing:
            print(f"❌ User already exists: {email}")
            print(f"   ID: {existing.get('_id')}")
            return
        
        # Create user with UUID
        user_id = str(uuid.uuid4())
        hashed = get_password_hash(password)
        
        user = {
            "_id": user_id,
            "email": email,
            "full_name": full_name,
            "hashed_password": hashed,
            "created_at": datetime.utcnow(),
            "is_active": True,
            "devices": [],
            "role": "user"
        }
        
        # Insert
        result = await db.db.users.insert_one(user)
        
        if result.inserted_id:
            print(f"✅ SUCCESS! User registered:")
            print(f"   Email: {email}")
            print(f"   User ID: {user_id}")
            print(f"   Full Name: {full_name}")
            print(f"\n🔐 You can now login with:")
            print(f"   Email: {email}")
            print(f"   Password: {password}")
        else:
            print("❌ Registration failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(register_user())