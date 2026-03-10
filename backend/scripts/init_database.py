#!/usr/bin/env python3
"""
Database initialization script
Creates indexes and initial collections
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import db
from src.config import settings

async def init_database():
    """Initialize database with indexes and collections"""
    print("Initializing database...")
    
    try:
        await db.connect()
        
        # Create indexes for better performance
        print("Creating indexes...")
        
        # Users collection indexes
        await db.db.users.create_index("email", unique=True)
        await db.db.users.create_index("created_at")
        
        # Devices collection indexes
        await db.db.devices.create_index("device_id", unique=True)
        await db.db.devices.create_index("user_id")
        await db.db.devices.create_index("pairing_status")
        
        # Usage data indexes
        await db.db.usage_data.create_index([("user_id", 1), ("timestamp", -1)])
        await db.db.usage_data.create_index([("device_id", 1), ("timestamp", -1)])
        await db.db.usage_data.create_index("timestamp", expireAfterSeconds=2592000)  # 30 days TTL
        
        # Notifications indexes
        await db.db.notifications.create_index([("user_id", 1), ("created_at", -1)])
        await db.db.notifications.create_index([("user_id", 1), ("read", 1)])
        
        # QR tokens indexes
        await db.db.qr_tokens.create_index("token", unique=True)
        await db.db.qr_tokens.create_index("expires_at", expireAfterSeconds=0)  # Auto-expire
        
        print("✅ Database initialized successfully!")
        
        # Create a test user for development
        await create_test_user()
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
    finally:
        await db.disconnect()

async def create_test_user():
    """Create a test user for development"""
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    test_user = {
        "_id": "test_user_001",
        "email": "test@fatigueguard.com",
        "full_name": "Test User",
        "hashed_password": pwd_context.hash("password123"),
        "created_at": "2024-01-01T00:00:00Z",
        "is_active": True,
        "devices": []
    }
    
    try:
        # Check if user already exists
        existing = await db.db.users.find_one({"email": test_user["email"]})
        if not existing:
            await db.db.users.insert_one(test_user)
            print("✅ Test user created: test@fatigueguard.com / password123")
        else:
            print("ℹ️ Test user already exists")
    except Exception as e:
        print(f"⚠️ Could not create test user: {e}")

if __name__ == "__main__":
    asyncio.run(init_database())