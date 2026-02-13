from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import connect_to_mongo, close_mongodb_connection
from mcp_rpc import MCPJsonRPC

from config import MONGODB_NAME, MONGODB_URL
# from core.orchestrator_agent import orchestrator_agent


# ================== Startup / Shutdown ==================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n🚀 Starting MCP Server...")
    await connect_to_mongo()

    print("✅ MCP Server Ready!\n")

    yield

    print("\n🛑 Shutting down...")
    await close_mongodb_connection()
    print("✅ Shutdown complete")


# ================== Create App ==================

app = FastAPI(
    title="Self-Learning MCP Server",
    version="1.0.0",
    lifespan=lifespan
)

# ================== CORS ==================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================== JSON-RPC MCP Setup ==================

rpc = MCPJsonRPC()


# ================== MCP REQUIRED METHODS ==================

async def initialize(params):
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "Self-Learning MCP Server",
            "version": "1.0.0"
        },
        "capabilities": {
            "tools": {
                "listChanged": False
            },
            "resources": {
                "listChanged": False
            }
        }
    }


async def ping(params):
    return {"status": "pong"}


async def resources_list(params):
    return {"resources": []}


rpc.register_method("initialize", initialize)
rpc.register_method("ping", ping)
rpc.register_method("resources/list", resources_list)


# ================== MCP TOOL LIST ==================

async def tools_list(params):
    return {
        "tools": [
            {
                "name": "analyze",
                "description": "Analyze content using Archestra LLM proxy",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "execute",
                "description": "Execute a task via orchestrator",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string"},
                        "agents": {"type": "array"}
                    },
                    "required": ["task"]
                }
            },
            {
                "name": "get_data",
                "description": "Fetch execution history from MongoDB",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer"}
                    }
                }
            }
        ]
    }


# ================== MCP TOOL CALL ==================

async def tool_call(params):
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    # ---- ANALYZE TOOL ----
    if tool_name == "analyze":
        content = arguments.get("content", "")

        if not content:
            return {"error": "content is required"}

        prompt = f"""
        Analyze this content:

        {content}

        Return clear insights.
        """

        result = await archestra_gateway.send_to_llm_proxy(prompt)

        return {"analysis": result}

    # ---- EXECUTE TOOL ----
    if tool_name == "execute":
        task = arguments.get("task", "")
        agents = arguments.get("agents", ["default"])

        if not task:
            return {"error": "task is required"}

        result = await orchestrator_agent.execute(task, agents)

        return {"result": result}

    # ---- GET DATA TOOL ----
    if tool_name == "get_data":
        from mcps.execution_tracker_mcp import execution_tracker

        limit = arguments.get("limit", 50)
        history = await execution_tracker.get_history(limit=limit)

        return {"history": history, "count": len(history)}

    return {"error": f"Unknown tool: {tool_name}"}


# Register MCP RPC methods
rpc.register_method("tools/list", tools_list)
rpc.register_method("tools/call", tool_call)


# ================== MCP JSON-RPC Endpoint ==================

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    return await rpc.handle(request)


# ================== Health Endpoint ==================

@app.get("/health")
async def health():
    stats = await get_stats()
    return {
        "status": "ok",
        "database_stats": stats
    }


# ================== Root Endpoint ==================

@app.get("/")
async def root():
    return {
        "message": "Self-Learning MCP Server Running",
        "json_rpc_endpoint": "/mcp"
    }
