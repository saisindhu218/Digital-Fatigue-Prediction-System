from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure
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
                serverSelectionTimeoutMS=15000,
                connectTimeoutMS=10000,
                socketTimeoutMS=15000
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
            await self._ensure_ttl_index(
                "usage_data", "timestamp", settings.USAGE_DATA_RETENTION_DAYS
            )

            # PREDICTIONS COLLECTION
            await self.db.predictions.create_index("user_id")
            await self._ensure_ttl_index(
                "predictions", "timestamp", settings.PREDICTIONS_RETENTION_DAYS
            )

            print(
                f"✅ Indexes created successfully "
                f"(usage_data/predictions auto-expire after "
                f"{settings.USAGE_DATA_RETENTION_DAYS}d)"
            )

        except Exception as e:

            print(f"⚠️ Index initialization warning: {e}")

    async def _ensure_ttl_index(self, collection_name: str, field: str, retention_days: int):
        """Creates (or fixes) a TTL index on `field` so documents older
        than `retention_days` are automatically deleted by MongoDB --
        no cron job or app code needed. If a plain (non-TTL) index on the
        same field already exists from before, MongoDB refuses to create
        a second index with different options on the same key, so we
        detect that conflict and swap it out for the TTL version."""

        collection = self.db[collection_name]
        expire_seconds = retention_days * 24 * 60 * 60

        try:
            await collection.create_index(field, expireAfterSeconds=expire_seconds)
        except OperationFailure as e:
            # code 85 = IndexOptionsConflict, code 86 = IndexKeySpecsConflict
            if getattr(e, "code", None) in (85, 86):
                old_index_name = f"{field}_1"
                try:
                    await collection.drop_index(old_index_name)
                except OperationFailure:
                    pass
                await collection.create_index(field, expireAfterSeconds=expire_seconds)
            else:
                raise

    def disconnect(self):

        if self.client:

            self.client.close()

            print("🔌 MongoDB connection closed")

            self.client = None
            self.db = None


# Global database instance
db = Database()