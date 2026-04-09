#!/usr/bin/env python3
"""
List users in the database
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from src.database import db

async def list_users():
    connected = await db.connect()
    if not connected:
        print("Failed to connect")
        return

    users = await db.db.users.find().to_list(length=None)
    print("Users in database:")
    for user in users:
        print(f"  ID: {user.get('_id')}, Email: {user.get('email')}, Username: {user.get('username')}")

    if db.client:
        db.client.close()

if __name__ == "__main__":
    asyncio.run(list_users())