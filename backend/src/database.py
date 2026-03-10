from motor.motor_asyncio import AsyncIOMotorClient
from src.config import settings


class Database:

    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):

        try:
            print("🔗 Connecting to MongoDB Atlas...")

            connection_string = settings.MONGODB_URL
            db_name = settings.DATABASE_NAME

            print(f"📊 Database name: {db_name}")

            self.client = AsyncIOMotorClient(
                connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )

            # Test connection
            await self.client.admin.command("ping")
            print("✅ MongoDB Atlas ping successful")

            self.db = self.client[db_name]

            collections = await self.db.list_collection_names()
            print(f"📂 Existing collections: {collections}")

            await self.initialize_collections()

            print("✅ Database connection successful")

            return True

        except Exception as e:

            print(f"❌ Database connection failed: {e}")
            self.client = None
            self.db = None

            return False

    async def initialize_collections(self):

        try:

            print("⚙️ Initializing collections and indexes...")

            # USERS COLLECTION
            await self.db.users.create_index("email", unique=True)

            # DEVICES COLLECTION
            await self.db.devices.create_index("user_id")
            await self.db.devices.create_index("device_id", unique=True)

            # USAGE DATA COLLECTION
            await self.db.usage_data.create_index("user_id")
            await self.db.usage_data.create_index("device_id")
            await self.db.usage_data.create_index("timestamp")

            # PREDICTIONS COLLECTION
            await self.db.predictions.create_index("user_id")
            await self.db.predictions.create_index("timestamp")

            print("✅ Indexes created successfully")

        except Exception as e:

            print(f"⚠️ Index initialization warning: {e}")

    async def disconnect(self):

        if self.client:

            self.client.close()

            print("🔌 MongoDB connection closed")

            self.client = None
            self.db = None


# Global database instance
db = Database()