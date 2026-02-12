from database import db 
from models import MemoryItem, LogItem
from typing import List 
from datetime import datetime 

class MemoryMCP:
    async def save_memory(self, memory: MemoryItem):
        data = memory.dict()
        await db.memory.insert_one(data)
        return {"saved": True, "memory": data}

    async def get_memory(self, agent_id: str, limit: int = 5): 
        cursor = db.memory.find({"agent_id": agent_id}).sort("timestamp", -1).limit(limit)
        results = await cursor.to_list(length=limit)
        return results

    async def search_memory(self, query: str, limit: int = 5): 
        cursor = db/memory.find({
            "$or": [
                {"task": { "$regex": query, "$options": "i"}},
                {"response": { "$regex": query, "$options": "i"}}
            ]
        }).sort("timestamp", -1).limit(limit)

        results = await cursor.to_list(length=limit)
        return results 

    async def save_log(self, log: LogItem):
        data = log.dict()
        await db.logs.insert_one(data)
        return {"saved": True, "log": data}

    async def get_logs(self, agent_id: str, limit: int = 10):
        cursor = db.logs.find({"agent_id": agent_id}).sort("timestamp", -1).limit(limit)
        results = await cursor.to_list(length=limit)
        return results 

memory_mcp = MemoryMCP()