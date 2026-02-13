from typing import Any, Dict
from fastapi import Request

class MCPJsonRPC:
    def __init__(self):
        self.methods = {}

    def register_method(self, name: str, func):
        self.methods[name] = func

    async def handle(self, request: Request) -> Dict[str, Any]:
        body = await request.json()

        jsonrpc = body.get("jsonrpc")
        method = body.get("method")
        params = body.get("params", {})
        rpc_id = body.get("id")

        if jsonrpc != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32600, "message": "Invalid JSON-RPC version"}
            }

        if method not in self.methods:
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"}
            }

        try:
            result = await self.methods[method](params)
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": result
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32000, "message": str(e)}
            }
