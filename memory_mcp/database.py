from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_NAME, MONGODB_URL

class Database: 
    client: AsyncIOMotorClient = None 
    db = None 

db = Database()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGODB_URL)
    db.db = db.client[MONGODB_NAME]

    # collections 
    db.memory = db.db["memory"]
    db.logs = db.db["logs"]

    # indexes 
    await db.memory.create_index("agent_id")
    await db.memory.create_index("task")
    await db.memory.create_index("timestamp")

    await db.logs.create_index("agent_id")
    await db.logs.create_index("timestamp")

    print("MongoDB connected")

async def close_mongodb_connection():
    if db.client: 
        db.client.close()
        print("MongoDB closed")