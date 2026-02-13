# json-rpc handler 

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

class MCPJsonRPC:
    def __init__(self): 
        self.method = {}

    def register_method(self, name: str, func): 
        self.method[name] = func 

    async def handle(self, request: Request):
        body = await request.json()

        method = body.get("method")
        params = body.get("params", {})
        rpc_id = body.get("id")

        if method not in self.methods: 
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32601,
                    "message": f"method '{method}' not found"
                }
            })

        try: 
            result = await self.methods[method][params]
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": result
            })
        except Exception as e: 
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            })