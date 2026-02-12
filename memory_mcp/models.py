from pydantic import BaseModel 
from typing import Optional, Dict, Any 
from datetime import datetime 

class MemoryItem(BaseModel): 
    agent_id: str 
    task: str 
    response: str 
    metadata: Optional[Dict[str, Any]] = {}
    timestamp: datetime = datetime.utcnow()

class LogItem(BaseModel): 
    agent_id: str 
    action: str
    status: str 
    details: Optional[Dict[str, Any]] = {}
    timestamp: datetime = datetime.utcnow()