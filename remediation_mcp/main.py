from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from database import connect_to_mongo, close_mongo_connection, get_stats, db
from mcp_roc import MCPJsonRPC


# ================== Startup / Shutdown ==================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n🚀 Starting REMEDIATION_TRACKER_MCP...")
    await connect_to_mongo()
    print("✅ MongoDB connected")
    print("✅ Remediation MCP Ready!\n")

    yield

    print("\n🛑 Shutting down...")
    await close_mongo_connection()
    print("✅ Shutdown complete")


# ================== Create App ==================

app = FastAPI(
    title="REMEDIATION_TRACKER_MCP",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"]
)


# ================== JSON-RPC Setup ==================

rpc = MCPJsonRPC()


# ================== Business Logic ==================

def estimate_cost_saved(severity_before: float):
    base_cost = 100_000
    multiplier = severity_before * 500_000
    return int(base_cost + multiplier)


def estimate_time_saved(minutes_to_fix: float):
    manual_hours = 700
    actual_hours = minutes_to_fix / 60
    return manual_hours, actual_hours


def calculate_effectiveness(before: float, after: float):
    if before <= 0:
        return 0.0
    improvement = ((before - after) / before) * 100
    return round(improvement, 2)


# ================== MCP REQUIRED METHODS ==================

async def initialize(params):
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "REMEDIATION_TRACKER_MCP",
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


# ================== MCP TOOLS LIST ==================

async def tools_list(params):
    return {
        "tools": [
            {
                "name": "track_remediation",
                "description": "Stores remediation logs + calculates cost/time saved + effectiveness",
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
                "description": "Returns remediation logs summary",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }


# ================== MCP TOOLS CALL ==================

async def tools_call(params):
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    # ---------------- TRACK REMEDIATION ----------------
    if tool_name == "track_remediation":
        vuln_type = arguments.get("vulnerability_type")
        severity_before = float(arguments.get("severity_before"))
        severity_after = float(arguments.get("severity_after"))
        time_to_fix_minutes = float(arguments.get("time_to_fix_minutes"))
        patch_status = arguments.get("patch_status")

        cost_saved = estimate_cost_saved(severity_before)

        manual_hours, actual_hours = estimate_time_saved(time_to_fix_minutes)
        time_saved_hours = round(manual_hours - actual_hours, 2)

        effectiveness = calculate_effectiveness(severity_before, severity_after)

        record = {
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
            "mongo_collection": "remediation_logs"
        }

    # ---------------- GET STATS ----------------
    if tool_name == "get_remediation_stats":
        total = await db.remediation_logs.count_documents({})
        latest = await db.remediation_logs.find().sort("timestamp", -1).limit(1).to_list(1)

        return {
            "total_remediations": total,
            "latest": latest[0] if latest else None
        }

    return {"error": f"Unknown tool: {tool_name}"}


rpc.register_method("tools/list", tools_list)
rpc.register_method("tools/call", tools_call)


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
        "service": "REMEDIATION_TRACKER_MCP",
        "database_stats": stats
    }


@app.get("/")
async def root():
    return {
        "message": "REMEDIATION_TRACKER_MCP running",
        "json_rpc_endpoint": "/mcp"
    }
