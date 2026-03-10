import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_database_connection():
    """Test MongoDB Atlas connection directly"""
    print("=" * 60)
    print("🔬 MongoDB Atlas Connection Test")
    print("=" * 60)
    
    try:
        from src.database import db
        from src.config import settings
        
        print(f"\n📁 Settings:")
        print(f"   Database name: {settings.DATABASE_NAME}")
        print(f"   Connection string: {settings.MONGODB_URL.split('@')[0]}@***")
        
        print(f"\n🔗 Attempting to connect...")
        await db.connect()
        
        if db.is_connected and db.db:
            print(f"\n✅ CONNECTION SUCCESSFUL!")
            
            # Test operations
            print(f"\n📊 Testing database operations:")
            
            # List collections
            collections = await db.db.list_collection_names()
            print(f"   Existing collections: {collections}")
            
            # Count users
            user_count = await db.db.users.count_documents({})
            print(f"   Total users: {user_count}")
            
            # Insert test document
            test_result = await db.db.test_collection.insert_one({"test": "connection", "timestamp": asyncio.get_event_loop().time()})
            print(f"   ✅ Write operation successful: {test_result.inserted_id}")
            
            # Read test document
            test_doc = await db.db.test_collection.find_one({"_id": test_result.inserted_id})
            print(f"   ✅ Read operation successful: {test_doc is not None}")
            
            # Delete test document
            await db.db.test_collection.delete_one({"_id": test_result.inserted_id})
            print(f"   ✅ Delete operation successful")
            
            print(f"\n🎉 All database operations working!")
            return True
        else:
            print(f"\n❌ CONNECTION FAILED!")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    finally:
        await db.disconnect()

if __name__ == "__main__":
    result = asyncio.run(test_database_connection())
    sys.exit(0 if result else 1)