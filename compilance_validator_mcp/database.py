from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_NAME, MONGODB_URL

class Database:
    client: AsyncIOMotorClient = None
    db = None 
    compilance_logs = None 

db = Database()

async def connect_to_mongo(): 
    db.client = AsyncIOMotorClient(MONGODB_URL)
    db.db = db.client[MONGODB_NAME]
    db.compilance_logs = db.db["compilance_logs"]

    await db.compilance_logs.create_index("timestamp")
    await db.compilance_logs.create_index("vulnerability_type")

    return True 

async def close_mongo_connection(): 
    if db.client:
        db.client.close()

async def get_stats():
    total = await db.compilance_logs.count_documents({})
    return total