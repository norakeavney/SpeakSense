"""MongoDB helper for SpeakSense API (pymongo)."""

import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from django.conf import settings

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """Singleton MongoDB connection manager."""
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
        return cls._instance

    def connect(self):
        """Establish connection to MongoDB."""
        if self._client is None:
            try:
                self._client = MongoClient(
                    settings.MONGODB_URI,
                    tls=False,
                    tlsAllowInvalidCertificates=False,
                    serverSelectionTimeoutMS=10000,
                )
                self._client.admin.command("ping")
                self._db = self._client[settings.MONGODB_DB_NAME]
                logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
                return True
            except ConnectionFailure as e:
                logger.error(f"MongoDB connection failed: {e}")
                return False
        return True

    def get_database(self):
        """Return the database instance, connecting if necessary."""
        if self._db is None:
            self.connect()
        return self._db

    def get_collection(self, collection_name):
        """Return a collection by name, or None if unavailable."""
        db = self.get_database()
        return db[collection_name] if db else None

    def close(self):
        """Close the MongoDB client and clear cached references."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")


# Global singleton instance
mongodb = MongoDBConnection()


def get_db():
    """Helper: get the database instance."""
    return mongodb.get_database()


def get_collection(collection_name):
    """Helper: get a collection by name."""
    return mongodb.get_collection(collection_name)
