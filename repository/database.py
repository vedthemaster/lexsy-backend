from motor.motor_asyncio import AsyncIOMotorClient

from config import config

client = AsyncIOMotorClient(config.DB_CONNECTION)
db = client[config.DB_NAME]
print("Database connected")