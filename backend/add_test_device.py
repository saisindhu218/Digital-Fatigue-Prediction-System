#!/usr/bin/env python3
"""
Add a test device to the database for testing the pairing page
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import uuid

# Add src to path
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from src.database import db
from src.config import settings

async def add_test_device():
    # Connect to database
    connected = await db.connect()
    if not connected:
        print("Failed to connect to database")
        return

    # Test user_id - update this to match your logged in user
    test_user_id = "e22fea91-efef-4c91-bbd3-fe1cf2c8f959"  # sindhu@gmail.com

    try:
        # Check if device already exists, update it
        existing = await db.db.devices.find_one({"device_id": "test-device-001"})
        if existing:
            await db.db.devices.update_one(
                {"device_id": "test-device-001"},
                {"$set": {"user_id": test_user_id}}
            )
            print("✅ Updated existing test device with correct user_id")
        else:
            # Create test device
            test_device = {
                "_id": str(uuid.uuid4()),
                "device_id": "test-device-001",
                "device_type": "laptop",
                "device_name": "Test Laptop",
                "user_id": test_user_id,
                "paired_at": datetime.utcnow(),
                "pairing_status": "paired",
                "last_active": datetime.utcnow()
            }

            # Insert device
            result = await db.db.devices.insert_one(test_device)
            print(f"✅ Test device added with ID: {result.inserted_id}")

        # Add some test usage data
        usage_data = {
            "_id": str(uuid.uuid4()),
            "user_id": test_user_id,
            "device_id": "test-device-001",
            "timestamp": datetime.utcnow(),
            "activity_type": "keyboard",
            "duration": 120,
            "fatigue_score": 45.5,
            "productivity_score": 85.2
        }

        await db.db.usage_data.insert_one(usage_data)
        print("✅ Test usage data added")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        if db.client:
            db.client.close()

if __name__ == "__main__":
    asyncio.run(add_test_device())