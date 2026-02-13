import os 
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient 

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_NAME", "mongodb://localhost:27017")
MONGODB_NAME = os.getenv("MONGODB_NAME", "archestra_mcp")

class Database: 
    client = AsyncIOMotorClient = None 
    db = None 
    remediation_logs = None 

db = Database()

async def connect_to_mongo(): 
    db.client = AsyncIOMotorClient(MONGODB_URL)
    db.db = db.client[MONGODB_NAME]
    db.remediation_logs = db.db["remediation_logs"]

    await db.remediation_logs.create_index("timestamp")
    await db.remediation_logs.create_index("vulnerability_type")
    await db.remediation_logs.create_index("patch_status")

async def close_mongo_connection(): 
    if db.client: 
        db.client.close()

async def get_stats(): 
    count = await db.remediation_logs.count_documents({})
    return { "remediation_count": count } 