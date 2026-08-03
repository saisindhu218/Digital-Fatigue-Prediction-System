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
            await self._deduplicate_devices()
            await self._ensure_unique_index("devices", "device_id")

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
    async def _ensure_unique_index(self, collection_name: str, field: str):
        """Same idea as _ensure_ttl_index but for a plain unique index --
        this one specifically fixes 'devices.device_id', which has been
        silently failing to become unique since a non-unique index with
        the same auto-generated name already existed in the live
        database from before this constraint was added. That silent
        failure (only ever logged as a startup warning, never actually
        fixed) is what allowed duplicate device_id documents to pile up,
        which in turn confused the connected-devices UI."""

        collection = self.db[collection_name]

        try:
            await collection.create_index(field, unique=True)
        except OperationFailure as e:
            if getattr(e, "code", None) in (85, 86):
                old_index_name = f"{field}_1"
                try:
                    await collection.drop_index(old_index_name)
                except OperationFailure:
                    pass
                await collection.create_index(field, unique=True)
            else:
                raise

    async def _deduplicate_devices(self):
        """One-time (repeats harmlessly every startup) cleanup: merges
        duplicate 'devices' documents that share the same device_id --
        a side effect of the unique index above never actually applying
        until now. Keeps whichever duplicate has the most recent
        last_heartbeat (falling back to last_active, then paired_at),
        deletes the rest. Required before the unique index can be
        created at all -- Mongo refuses a unique index while duplicates
        still exist."""

        try:
            duplicates_cursor = self.db.devices.aggregate([
                {"$group": {
                    "_id": "$device_id",
                    "ids": {"$push": "$_id"},
                    "count": {"$sum": 1},
                }},
                {"$match": {"count": {"$gt": 1}}},
            ])
            duplicate_groups = await duplicates_cursor.to_list(length=None)

            for group in duplicate_groups:
                device_id = group["_id"]
                if not device_id:
                    continue

                docs_cursor = self.db.devices.find({"device_id": device_id})
                docs = await docs_cursor.to_list(length=None)

                def sort_key(d):
                    return (
                        d.get("last_heartbeat")
                        or d.get("last_active")
                        or d.get("paired_at")
                    )

                docs_with_dates = [d for d in docs if sort_key(d) is not None]
                docs_without_dates = [d for d in docs if sort_key(d) is None]

                if docs_with_dates:
                    docs_with_dates.sort(key=sort_key, reverse=True)
                    keep = docs_with_dates[0]
                    remove = docs_with_dates[1:] + docs_without_dates
                else:
                    keep = docs[0]
                    remove = docs[1:]

                remove_ids = [d["_id"] for d in remove]
                if remove_ids:
                    await self.db.devices.delete_many({"_id": {"$in": remove_ids}})
                    print(
                        f"🧹 Merged {len(remove_ids)} duplicate device record(s) "
                        f"for device_id={device_id}, kept most recent"
                    )
        except Exception as e:
            print(f"⚠️ Device deduplication warning (non-fatal): {e}")


    def disconnect(self):

        if self.client:

            self.client.close()

            print("🔌 MongoDB connection closed")

            self.client = None
            self.db = None


# Global database instance
db = Database()