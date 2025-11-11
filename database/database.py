"""
Shared database connection for all API versions.
Both v1 and v2 can import from this module.
"""

from motor.motor_asyncio import AsyncIOMotorClient

from config import config

client = AsyncIOMotorClient(config.DB_CONNECTION)
db = client[config.DB_NAME]
print("Database connected")
