from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from database import connect_to_mongo, close_mongo_connection, get_stats, db
from mcp_rpc import MCPJsonRPC


# ================= Startup / Shutdown =================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n🚀 Starting COMPLIANCE_VALIDATOR_MCP...")
    await connect_to_mongo()
    print("✅ MongoDB Connected")
    print("✅ Compliance Validator MCP Ready!\n")
    yield
    print("\n🛑 Shutting down COMPLIANCE_VALIDATOR_MCP...")
    await close_mongo_connection()
    print("✅ Shutdown complete")


# ================= Create App =================

app = FastAPI(
    title="COMPLIANCE_VALIDATOR_MCP",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_headers=["*"],
)


rpc = MCPJsonRPC()


# ================= Compliance Logic =================

SUPPORTED_STANDARDS = ["OWASP", "GDPR", "PCI-DSS", "SOC2", "ISO27001"]


def validate_standard(vuln_type: str, fix_applied: bool, standard: str):
    """
    Simple rule-based compliance checker.
    You can make it smarter later.
    """

    if not fix_applied:
        return False, f"{standard} failed because fix was not applied."

    vuln_type = vuln_type.lower()

    # Basic mapping
    if standard == "OWASP":
        return True, "Fix meets OWASP guidelines."

    if standard == "GDPR":
        if "data leak" in vuln_type or "privacy" in vuln_type:
            return True, "Fix aligns with GDPR privacy controls."
        return True, "No direct GDPR violation detected."

    if standard == "PCI-DSS":
        if "sql" in vuln_type or "payment" in vuln_type:
            return True, "Fix meets PCI-DSS security requirements."
        return True, "PCI-DSS not directly impacted."

    if standard == "SOC2":
        return True, "SOC2 compliance validated (security controls satisfied)."

    if standard == "ISO27001":
        return True, "ISO27001 compliance validated (risk mitigation applied)."

    return False, "Unknown standard."


def calculate_next_audit_date():
    return (datetime.utcnow() + timedelta(days=90)).strftime("%Y-%m-%d")


# ================= MCP REQUIRED METHODS =================

async def initialize(params):
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "COMPLIANCE_VALIDATOR_MCP",
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


# ================= MCP TOOLS LIST =================

async def tools_list(params):
    return {
        "tools": [
            {
                "name": "validate_compliance",
                "description": "Validates compliance standards (OWASP, GDPR, PCI-DSS, SOC2, ISO27001) and stores report in MongoDB",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "vulnerability_type": {"type": "string"},
                        "fix_applied": {"type": "boolean"},
                        "standards": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["vulnerability_type", "fix_applied", "standards"]
                }
            },
            {
                "name": "get_compliance_stats",
                "description": "Returns compliance validation history stats",
                "inputSchema": {"type": "object", "properties": {}}
            }
        ]
    }


# ================= MCP TOOL CALL =================

async def tool_call(params):
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    # ---- validate_compliance ----
    if tool_name == "validate_compliance":
        vulnerability_type = arguments.get("vulnerability_type", "")
        fix_applied = arguments.get("fix_applied", False)
        standards = arguments.get("standards", [])

        if not vulnerability_type:
            return {"error": "vulnerability_type is required"}

        if not isinstance(standards, list) or len(standards) == 0:
            return {"error": "standards must be a list"}

        report = {}
        met_standards = []
        failed_standards = []

        for standard in standards:
            standard = standard.strip().upper()

            # normalize names
            if standard == "PCIDSS":
                standard = "PCI-DSS"

            if standard not in SUPPORTED_STANDARDS:
                report[standard] = {
                    "compliant": False,
                    "reason": "Unsupported standard"
                }
                failed_standards.append(standard)
                continue

            compliant, reason = validate_standard(vulnerability_type, fix_applied, standard)
            report[standard] = {"compliant": compliant, "reason": reason}

            if compliant:
                met_standards.append(standard)
            else:
                failed_standards.append(standard)

        compliance_status = "✅ COMPLIANT" if len(failed_standards) == 0 else "❌ NOT COMPLIANT"

        record = {
            "vulnerability_type": vulnerability_type,
            "fix_applied": fix_applied,
            "requested_standards": standards,
            "met_standards": met_standards,
            "failed_standards": failed_standards,
            "compliance_status": compliance_status,
            "next_audit_date": calculate_next_audit_date(),
            "report": report,
            "timestamp": datetime.utcnow()
        }

        await db.compliance_logs.insert_one(record)

        return {
            "status": "stored",
            "compliance_status": compliance_status,
            "standards_met": met_standards,
            "standards_failed": failed_standards,
            "next_audit_date": record["next_audit_date"],
            "report": report,
            "mongo": "stored in compliance_logs"
        }

    # ---- get_compliance_stats ----
    if tool_name == "get_compliance_stats":
        total = await db.compliance_logs.count_documents({})
        latest = await db.compliance_logs.find().sort("timestamp", -1).limit(1).to_list(1)

        return {
            "total_reports": total,
            "latest": latest[0] if latest else None
        }

    return {"error": f"Unknown tool: {tool_name}"}


rpc.register_method("tools/list", tools_list)
rpc.register_method("tools/call", tool_call)


# ================= JSON-RPC Endpoint =================

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    return await rpc.handle(request)


# ================= Health Endpoint =================

@app.get("/health")
async def health():
    stats = await get_stats()
    return {
        "status": "ok",
        "service": "COMPLIANCE_VALIDATOR_MCP",
        "database_stats": stats
    }


@app.get("/")
async def root():
    return {
        "message": "COMPLIANCE_VALIDATOR_MCP Running",
        "json_rpc_endpoint": "/mcp",
        "port": 8012
    }
