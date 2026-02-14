from fastapi import Request
from fastapi.responses import JSONResponse


class MCPJsonRPC:
    def __init__(self):
        self.methods = {}

    def register_method(self, name: str, func):
        self.methods[name] = func

    async def handle(self, request: Request):
        body = await request.json()

        jsonrpc = body.get("jsonrpc", "2.0")
        method = body.get("method")
        params = body.get("params", {})
        rpc_id = body.get("id")

        if method not in self.methods:
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": jsonrpc,
                    "id": rpc_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            )

        try:
            result = await self.methods[method](params)

            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": jsonrpc,
                    "id": rpc_id,
                    "result": result
                }
            )

        except Exception as e:
            return JSONResponse(
                status_code=200,
                content={
                    "jsonrpc": jsonrpc,
                    "id": rpc_id,
                    "error": {
                        "code": -32000,
                        "message": str(e)
                    }
                }
            )
