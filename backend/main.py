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

@app.get("/api/mcp/info")
async def mcp_info():
    """MCP server information"""
    return {
        "name": "Self-Learning Agent System",
        "version": "1.0.0",
        "status": "ready",
        "type": "mcp_server",
        "mcps": [
            {
                "name": "ExecutionTracker",
                "description": "Tracks all agent executions"
            },
            {
                "name": "PatternLearner",
                "description": "Learns patterns from execution data"
            },
            {
                "name": "Optimizer",
                "description": "Suggests workflow optimizations"
            },
            {
                "name": "QualityValidator",
                "description": "Validates output quality"
            },
            {
                "name": "AgentScorer",
                "description": "Scores agents based on performance"
            }
        ],
        "capabilities": [
            "self-learning",
            "pattern-recognition",
            "optimization",
            "quality-validation",
            "agent-scoring"
        ]
    }

@app.get("/api/mcp/capabilities")
async def mcp_capabilities():
    """MCP capabilities"""
    return {
        "name": "Self-Learning Agent System",
        "version": "1.0.0",
        "status": "ready",
        "endpoints": [
            "/api/health",
            "/api/mcp/info",
            "/api/mcp/capabilities",
            "/api/mcp/execute-task",
            "/api/mcp/analyze",
            "/api/mcp/optimize"
        ]
    }

# ========== MCP EXECUTION ENDPOINTS ==========

@app.post("/api/mcp/execute-task")
async def mcp_execute_task(task_data: dict):
    """Execute a task through orchestrator"""
    task = task_data.get("task", "")
    agents = task_data.get("agents", [])
    
    try:
        result = await orchestrator_agent.execute(task, agents)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/mcp/analyze")
async def mcp_analyze(data: dict):
    """Analyze data using LLM"""
    content = data.get("content", "")
    analysis_type = data.get("type", "general")
    
    prompt = f"""
    Analyze this {analysis_type}:
    
    {content}
    
    Provide insights.
    """
    
    result = await archestra_gateway.send_to_llm_proxy(prompt)
    
    return {
        "status": "success",
        "analysis": result
    }

@app.post("/api/mcp/optimize")
async def mcp_optimize(workflow_data: dict):
    """Optimize workflows"""
    from mcps.pattern_learner_mcp import pattern_learner
    from mcps.optimizer_mcp import optimizer
    
    workflow = workflow_data.get("workflow", [])
    history = workflow_data.get("history", [])
    
    patterns = await pattern_learner.learn(history) if history else {}
    suggestions = await optimizer.suggest_optimization(
        workflow=workflow,
        execution_history=history,
        goal="balanced"
    ) if history else []
    
    return {
        "status": "success",
        "patterns": patterns,
        "suggestions": suggestions[:3]
    }

# ========== ARCHESTRA INTEGRATION ENDPOINTS ==========

@app.get("/api/archestra/status")
async def archestra_status():
    """Archestra integration status"""
    is_online = await archestra_gateway.check_archestra_health()
    return {
        "archestra_online": is_online,
        "mcp_gateway": archestra_gateway.mcp_url,
        "llm_proxy": archestra_gateway.llm_url,
        "a2a_gateway": archestra_gateway.a2a_url,
        "auth_token": "✓ Configured"
    }

# ========== DATABASE ENDPOINTS ==========

@app.get("/api/database/stats")
async def database_stats():
    """Database statistics"""
    stats = await get_stats()
    return {
        "status": "success",
        "stats": stats
    }

# ========== EXECUTION HISTORY ENDPOINTS ==========

@app.get("/api/execution-stats/{agent_id}")
async def get_execution_stats(agent_id: str):
    """Get execution statistics for agent"""
    from mcps.execution_tracker_mcp import execution_tracker
    stats = await execution_tracker.get_stats(agent_id)
    return {
        "status": "success",
        "agent_id": agent_id,
        "stats": stats
    }

@app.get("/api/learning-insights")
async def get_learning_insights():
    """Get what the system has learned"""
    from mcps.execution_tracker_mcp import execution_tracker
    history = await execution_tracker.get_history(limit=100)
    return {
        "status": "success",
        "total_executions": len(history),
        "message": "System learns from every execution"
    }

@app.get("/api/agent-scores")
async def get_agent_scores():
    """Get all agent scores and rankings"""
    from mcps.agent_scorer_mcp import agent_scorer
    scores = await agent_scorer.score_all_agents()
    return {
        "status": "success",
        "agents": scores
    }

# ========== EXECUTION ENDPOINT ==========

@app.post("/api/execute-optimized")
async def execute_optimized_workflow(task: str, agents: list):
    """Execute workflow with self-learning optimization"""
    try:
        result = await orchestrator_agent.execute(task, agents)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }