import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_connection():
    from database import db
    from config import settings
    
    print(f"Testing connection to: {settings.MONGODB_URL[:50]}...")
    print(f"Database: {settings.DATABASE_NAME}")
    
    try:
        await db.connect()
        print("✅ Async connection successful!")
        
        # Test a simple operation
        users = await db.db.users.find().to_list(length=5)
        print(f"Found {len(users)} users in database")
        
        await db.disconnect()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())