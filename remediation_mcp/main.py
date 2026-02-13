from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from database import connect_to_mongo, close_mongo_connection, get_stats
from mcp_roc import MCPJsonRPC

# startup / shutdown

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n🚀 Starting remediation mcp...")
    await connect_to_mongo()
    print("✅ MongoDB connected")
    print("✅ Remediation tracker mcp ready")
    yield
    print("\n🛑 Shutting down")
    await close_mongo_connection()
    print("✅ Shutdown complete")

# create app 

app = FastAPI(
    title="Remediation_tracker_mcp",
    version="1.0.0",
    lifespan=lifespan
)

app.add.middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"]
)

rpc = MCPJsonRPC()

# business logic 

def estimate_cost_saved(severity_before: float):
    base_cost = 1_00_000
    multiplier = severity_before * 5_00_000
    return int(base_cost * multiplier)

def estimate_time_saved(minutes_to_fix: float):
    manual_hours = 700
    actual_hours = minutes_to_fix / 60 
    return manual_hours, actual_hours

def calculate_effeciveness(before: float, after: float):
    if before <= 0: 
        return 0.0
    improvement = ((before - after) / before) * 100
    return round(improvement, 2)

# mcp required method 

async def initialize(params):
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "REMEDIATION_TRACKER_MCP",
            "version": "1.0.0"
        },
        "capabilities": {
            "tools": {},
            "resources": {}
        }
    }

async def ping(params):
    return {"status": "pong"}

async def resource_list(params):
    return {"resource": []}

# mcp tool 

async def tools_list(params):
    return {
        "tools": [
            {
                "name": "track_remediation",
                "description": "Track vulnerability fix, calculate metrics, store in MongoDB",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vulnerability_type": {"type": "string"},
                        "severity_before": {"type": "number"},
                        "severity_after": {"type": "number"},
                        "time_to_fix_minutes": {"type": "number"},
                        "patch_status": {"type": "string"}
                    },
                    "required": [
                        "vulnerability_type",
                        "severity_before",
                        "severity_after",
                        "time_to_fix_minutes",
                        "patch_status"
                    ]
                }
            },
            {
                "name": "get_remediation_stats",
                "description": "Get stored remediation stats summary",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]
    }

async def tools_call(params):
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name == "track_remediation":
        vuln_type = arguments.get("vulnerability_type")
        severity_before = float(arguments.get("severity_before"))
        severity_after = float(arguments.get("severity_after"))
        time_to_fix_minutes = float(arguments.get("time_to_fix_minutes"))
        patch_status = arguments.get("patch_status")

        cost_saved = estimate_cost_saved(severity_before)
        
        manual_hours, actual_hours = estimate_time_saved(time_to_fix_minutes)
        time_saved_hours = round(manual_hours - actual_hours, 2)

        effectiveness = calculate_effeciveness(severity_before, severity_after)

        record={
            "vulnerability_type": vuln_type,
            "severity_before": severity_before,
            "severity_after": severity_after,
            "time_to_fix_minutes": time_to_fix_minutes,
            "patch_status": patch_status,
            "cost_saved": cost_saved,
            "manual_hours_estimate": manual_hours,
            "actual_hours": actual_hours,
            "time_saved_hours": time_saved_hours,
            "effectiveness_percent": effectiveness,
            "timestamp": datetime.utcnow()
        }

        await db.remediation_logs.insert_one(record)

        return {
            "status": "stored",
            "vulnerability_type": vuln_type,
            "patch_status": patch_status,
            "cost_saved": f"${cost_saved:,}",
            "time_saved": f"{time_saved_hours} hours vs {time_to_fix_minutes} minutes",
            "effectiveness": f"{effectiveness}% better",
            "mongo": "stored in remediation_logs"
        }

        if tool_name == "get_remediation_stats":
            total = await db.remediation_logs.count_documents({})
            latest = await db.remediation_logs.find().sort("timestamp", -1).limit(1).to_list(1)

            return {
                "total_remediation": total,
                "latest": latest[0] if latest else None 
            }

        return {"error": f"Unknown tool: {tool_name}"}

# register method 

rpc.register_method("initialize", initialize)
rpc.register_method("ping", ping)
rpc.register_method("resource_list", resource_list)
rpc.register_method("tools_list", tools_list)
rpc.register_method("tools_call", tools_call)

# mcp json-rpc endpoint 
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    return await rpc.handle(request)


# health 
@app.get("/health")
async def health():
    stats = await get_stats()
    return {
        "status": "ok",
        "service": "Remediation_tracker_mcp",
        "stats": stats
    }
