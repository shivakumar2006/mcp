from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import connect_to_mongo, close_mongodb_connection
from mcps.memory_mcp import memory_mcp
from models import MemoryItem, LogItem

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongodb_connection()

app = FastAPI(
    title = "memory MCP server",
    version = "1.0.0",
    lifespan=lifespan
)

# cors 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "running", "service": "Memory MCP"}

@app.get("/archestra_mcp/tools")
async def tools(): 
    return {
        "tools": [
            {
                "name": "save_memory",
                "description": "Save memory for an agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type", "string"},
                        "task": {"type", "string"},
                        "response": {"type", "string"},
                        "metadata": {"type", "string"}
                    },
                    "required": ["agent_id", "task", "response"]
                }
            },
            {
                "name": "get_memory",
                "description": "Get last memories for an agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "limit": {"type": "integer"}
                    },
                    "required": ["agent_id"]
                }
            },
            {
                "name": "search_memory",
                "description": "Search memory by query text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "save_log",
                "description": "Save execution log",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "action": {"type": "string"},
                        "status": {"type": "string"},
                        "details": {"type": "object"}
                    },
                    "required": ["agent_id", "action", "status"]
                }
            },
            {
                "name": "get_logs",
                "description": "Get logs for agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "limit": {"type": "integer"}
                    },
                    "required": ["agent_id"]
                }
            }
        ]
    }