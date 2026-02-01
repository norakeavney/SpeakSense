"""
MongoDB connection handler for SpeakSense
Provides both synchronous and asynchronous database connections
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from motor.motor_asyncio import AsyncIOMotorClient
from decouple import config


class MongoDBConnection:
    """MongoDB connection handler for SpeakSense"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.async_client = None
        self.async_db = None
        self._mongodb_uri = config('MONGODB_URI')
        self._db_name = config('MONGODB_DB_NAME', default='speaksense_db')
        
    def connect(self):
        """Connect to MongoDB (synchronous)"""
        if self.db is not None:
            return self.db
            
        try:
            # Add SSL/TLS settings for Python 3.12+ compatibility
            self.client = MongoClient(
                self._mongodb_uri,
                tlsAllowInvalidCertificates=True,  # For development/testing
                serverSelectionTimeoutMS=10000
            )
            self.db = self.client[self._db_name]
            
            # Test connection
            self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {self._db_name}")
            return self.db
            
        except ConnectionFailure as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise
    
    async def async_connect(self):
        """Connect to MongoDB (asynchronous - for async operations)"""
        if self.async_db is not None:
            return self.async_db
            
        try:
            # Add SSL/TLS settings for Python 3.12+ compatibility
            self.async_client = AsyncIOMotorClient(
                self._mongodb_uri,
                tlsAllowInvalidCertificates=True,  # For development/testing
                serverSelectionTimeoutMS=10000
            )
            self.async_db = self.async_client[self._db_name]
            
            # Test connection
            await self.async_client.admin.command('ping')
            print(f"✅ Async connected to MongoDB: {self._db_name}")
            return self.async_db
            
        except Exception as e:
            print(f"❌ Async MongoDB connection failed: {e}")
            raise
    
    def get_collection(self, collection_name):
        """Get a specific collection (synchronous)"""
        if not self.db:
            self.connect()
        return self.db[collection_name]
    
    def close(self):
        """Close MongoDB connections"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
        if self.async_client:
            self.async_client.close()
            self.async_client = None
            self.async_db = None
        print("MongoDB connections closed")


# Global instance
mongodb = MongoDBConnection()


# Helper functions for easy access
def get_db():
    """Get the database instance"""
    return mongodb.connect()


def get_collection(collection_name):
    """Get a specific collection"""
    return mongodb.get_collection(collection_name)
