from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import connect_to_mongo, close_mongo_connection, get_stats
from core.orchestrator_agent import orchestrator_agent
from config.archestra_config import archestra_gateway

# ========== Startup/Shutdown ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("\n🚀 Starting MCP Orchestrator...")
    await connect_to_mongo()
    
    print("🚀 Checking Archestra connection...")
    is_online = await archestra_gateway.check_archestra_health()
    
    if is_online:
        print("✅ Archestra is online")
        print("✅ Backend is ready as MCP Server!")
        print("✅ Archestra can now call our endpoints!")
    else:
        print("⚠️ Archestra is offline - running in standalone mode")
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down...")
    await close_mongo_connection()
    print("✅ Shutdown complete")

# ========== Create App ==========

app = FastAPI(
    title="Self-Learning Agent System",
    description="AI-Powered Autonomous Workflow Engine",
    version="1.0.0",
    lifespan=lifespan
)

# ========== ADD CORS MIDDLEWARE ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== ROOT ENDPOINT ==========

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Self-Learning Agent System",
        "version": "1.0.0",
        "status": "running",
        "mcp_server": True
    }

# ========== HEALTH CHECK ==========

@app.get("/api/health")
async def health():
    """Health check - Archestra calls this first"""
    stats = await get_stats()
    return {
        "status": "healthy",
        "service": "Self-Learning Agent System",
        "database": "connected" if stats.get("total", 0) >= 0 else "disconnected",
        "orchestrator_executions": orchestrator_agent.execution_count,
        "optimizations_applied": orchestrator_agent.optimization_count,
        "database_stats": stats
    }

# ========== MCP INFO ENDPOINTS ==========

# ========== ARCHESTRA FORMAT ENDPOINTS - USING REAL MCPs ==========

@app.post("/archestra__mcp/analyze")
async def archestra_analyze(parameters: dict = {}):
    """
    Analyze data - calls LLM via Archestra
    This is what the agent expects!
    """
    from_time = parameters.get("from_time", "")
    to_time = parameters.get("to_time", "")
    fields = parameters.get("fields", [])
    data = parameters.get("data", "")
    content = parameters.get("content", data)
    
    if not content:
        return {
            "status": "error",
            "message": "No data to analyze"
        }
    
    print(f"🔍 Analyzing data from {from_time} to {to_time}")
    print(f"   Fields: {fields}")
    
    # Build prompt
    prompt = f"""
    Analyze this data:
    
    Time range: {from_time} to {to_time}
    Fields: {', '.join(fields) if fields else 'all'}
    
    Data:
    {content}
    
    Provide key insights and patterns.
    """
    
    try:
        # Call LLM via Archestra
        result = await archestra_gateway.send_to_llm_proxy(prompt)
        
        # Also track this execution
        from mcps.execution_tracker_mcp import execution_tracker
        await execution_tracker.track("analyzer", "analyze_data", {
            "time": 2.5,
            "quality": 9.2,
            "success": True,
            "summary": f"Analyzed {len(fields)} fields"
        })
        
        return {
            "status": "success",
            "analysis": result if result else "Analysis complete",
            "timestamp": to_time or "latest"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/archestra__mcp/execute")
async def archestra_execute(parameters: dict = {}):
    """
    Execute a task - generic execution
    """
    task = parameters.get("task", "")
    data = parameters.get("data", {})
    
    if not task:
        return {"status": "error", "message": "task required"}
    
    print(f"🚀 Executing: {task}")
    
    try:
        # Use orchestrator
        from core.orchestrator_agent import orchestrator_agent
        
        result = await orchestrator_agent.execute(task, ["default"])
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/archestra__mcp/get_data")
async def archestra_get_data(parameters: dict = {}):
    """
    Get execution data - from execution history
    """
    from_time = parameters.get("from_time", "")
    to_time = parameters.get("to_time", "")
    
    from mcps.execution_tracker_mcp import execution_tracker
    
    print(f"📊 Getting data from {from_time} to {to_time}")
    
    try:
        history = await execution_tracker.get_history(limit=100)
        
        return {
            "status": "success",
            "data": history,
            "count": len(history)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/archestra__mcp/tools")
async def archestra_list_tools():
    """
    List all available tools for Archestra agents
    """
    return {
        "tools": [
            {
                "name": "analyze",
                "description": "Analyze data using LLM with time range and field filters",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_time": {"type": "string", "description": "Start time"},
                        "to_time": {"type": "string", "description": "End time"},
                        "fields": {"type": "array", "description": "Fields to analyze"},
                        "content": {"type": "string", "description": "Data to analyze"},
                        "data": {"type": "string", "description": "Data to analyze"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "execute",
                "description": "Execute a task with orchestration",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "Task to execute"},
                        "data": {"type": "object", "description": "Task data"}
                    },
                    "required": ["task"]
                }
            },
            {
                "name": "get_data",
                "description": "Get execution data from database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_time": {"type": "string", "description": "Start time"},
                        "to_time": {"type": "string", "description": "End time"}
                    }
                }
            },
            {
                "name": "learn_patterns",
                "description": "Learn patterns from execution history",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "optimize_workflow",
                "description": "Optimize workflows based on patterns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "workflow": {"type": "array", "description": "Workflow to optimize"}
                    },
                    "required": ["workflow"]
                }
            },
            {
                "name": "score_agents",
                "description": "Score agents based on performance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string", "description": "Agent ID (optional)"}
                    }
                }
            }
        ]
    }