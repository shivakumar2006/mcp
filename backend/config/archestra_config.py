# Copy-paste this EXACTLY

import os
from dotenv import load_dotenv

load_dotenv()

# Archestra Configuration
ARCHESTRA_CONFIG = {
    "mcp_gateway_url": os.getenv(
        "ARCHESTRA_MCP_GATEWAY",
        "http://localhost:9000/v1/mcp/db5f9366-33e7-4907-8964-97c4b13dcc67"
    ),
    "llm_proxy_url": os.getenv(
        "ARCHESTRA_LLM_PROXY",
        "http://localhost:9000/v1/ollama/e226125f-4fca-4859-8936-89385214ce3a"
    ),
    "a2a_gateway_url": os.getenv(
        "ARCHESTRA_A2A_GATEWAY",
        "http://localhost:9000/v1/a2a/515d0e56-712e-4965-b39a-93d57050d2b4"
    ),
    "auth_token": os.getenv(
        "ARCHESTRA_AUTH_TOKEN",
        "archestra_16e49b28d65890a7bff2c0a738ac2843"
    ),
    "base_url": os.getenv(
        "ARCHESTRA_BASE_URL",
        "http://localhost:9000"
    )
}

class ArchestraGateway:
    """
    Gateway to call Archestra services (LLM, A2A)
    We DON'T register - we just USE them!
    """
    
    def __init__(self):
        self.mcp_url = ARCHESTRA_CONFIG["mcp_gateway_url"]
        self.llm_url = ARCHESTRA_CONFIG["llm_proxy_url"]
        self.a2a_url = ARCHESTRA_CONFIG["a2a_gateway_url"]
        self.token = ARCHESTRA_CONFIG["auth_token"]
        
        # Headers for Archestra
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
    
    async def send_to_llm_proxy(self, prompt: str) -> str:
        """
        Send request to Archestra LLM Proxy (Ollama/Llama3.2)
        """
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.llm_url,
                    json={
                        "model": "llama3.2:3b",
                        "prompt": prompt,
                        "stream": False,
                        "temperature": 0.3
                    },
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    llm_response = data.get("response", "")
                    print(f"✅ LLM Proxy response ({len(llm_response)} chars)")
                    return llm_response
                else:
                    print(f"❌ LLM Proxy error: {response.text}")
                    return None
        except Exception as e:
            print(f"❌ Error calling LLM Proxy: {e}")
            return None
    
    async def check_archestra_health(self) -> bool:
        """
        Check if Archestra is online
        """
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{ARCHESTRA_CONFIG['base_url']}/health",
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if response.status_code == 200:
                    print("✅ Archestra is online")
                    return True
                else:
                    print("⚠️ Archestra health check failed")
                    return False
        except Exception as e:
            print(f"⚠️ Cannot reach Archestra: {e}")
            return False

# Create global instance
archestra_gateway = ArchestraGateway()



# # Copy-paste this EXACTLY

# import os
# from dotenv import load_dotenv
# import json

# load_dotenv()

# # Archestra Configuration
# ARCHESTRA_CONFIG = {
#     "mcp_gateway_url": os.getenv(
#         "ARCHESTRA_MCP_GATEWAY",
#         "http://localhost:9000/v1/mcp/db5f9366-33e7-4907-8964-97c4b13dcc67"
#     ),
#     "llm_proxy_url": os.getenv(
#         "ARCHESTRA_LLM_PROXY",
#         "http://localhost:9000/v1/ollama/e226125f-4fca-4859-8936-89385214ce3a"
#     ),
#     "a2a_gateway_url": os.getenv(
#         "ARCHESTRA_A2A_GATEWAY",
#         "http://localhost:9000/v1/a2a/515d0e56-712e-4965-b39a-93d57050d2b4"
#     ),
#     "auth_token": os.getenv(
#         "ARCHESTRA_AUTH_TOKEN",
#         "archestra_16e49b28d65890a7bff2c0a738ac2843"
#     ),
#     "base_url": os.getenv(
#         "ARCHESTRA_BASE_URL",
#         "http://localhost:9000"
#     )
# }

# class ArchestraGateway:
#     """
#     Gateway to communicate with Archestra
#     Uses JSON-RPC 2.0 protocol
#     """
    
#     def __init__(self):
#         self.mcp_url = ARCHESTRA_CONFIG["mcp_gateway_url"]
#         self.llm_url = ARCHESTRA_CONFIG["llm_proxy_url"]
#         self.a2a_url = ARCHESTRA_CONFIG["a2a_gateway_url"]
#         self.token = ARCHESTRA_CONFIG["auth_token"]
        
#         # Headers for Archestra
#         self.headers = {
#             "Authorization": f"Bearer {self.token}",
#             "Content-Type": "application/json",
#             "Accept": "application/json, text/event-stream",
#         }
        
#         self.request_id = 0
    
#     def _get_request_id(self):
#         """Get unique request ID"""
#         self.request_id += 1
#         return self.request_id
    
#     def _build_jsonrpc_request(self, method: str, params: dict) -> dict:
#         """
#         Build JSON-RPC 2.0 compliant request
#         """
#         return {
#             "jsonrpc": "2.0",
#             "method": method,
#             "params": params,
#             "id": self._get_request_id()
#         }
    
#     async def send_to_mcp_gateway(self, data: dict) -> dict:
#         """
#         Send data through MCP Gateway using JSON-RPC
#         """
#         import httpx
        
#         try:
#             # Build JSON-RPC request
#             jsonrpc_request = self._build_jsonrpc_request(
#                 method="process",
#                 params=data
#             )
            
#             print(f"📤 Sending to MCP Gateway: {jsonrpc_request}")
            
#             async with httpx.AsyncClient(timeout=30.0) as client:
#                 response = await client.post(
#                     self.mcp_url,
#                     json=jsonrpc_request,
#                     headers=self.headers
#                 )
                
#                 print(f"📥 MCP Gateway response: {response.status_code}")
                
#                 if response.status_code in [200, 201]:
#                     try:
#                         result = response.json()
#                         if "result" in result:
#                             print(f"✅ MCP Gateway success")
#                             return result["result"]
#                         elif "error" in result:
#                             print(f"❌ MCP Gateway error: {result['error']}")
#                             return {"error": result["error"]}
#                         else:
#                             print(f"✅ MCP Gateway response received")
#                             return result
#                     except:
#                         print(f"✅ MCP Gateway response (non-JSON)")
#                         return {"status": "success", "message": response.text}
#                 else:
#                     print(f"❌ MCP Gateway HTTP error: {response.text}")
#                     return {"error": response.text}
#         except Exception as e:
#             print(f"❌ Error sending to MCP Gateway: {e}")
#             return {"error": str(e)}
    
#     async def send_to_llm_proxy(self, prompt: str) -> str:
#         """
#         Send request to Archestra LLM Proxy (Ollama/Llama3.2)
#         Using JSON-RPC
#         """
#         import httpx
        
#         try:
#             # Build JSON-RPC request for LLM
#             jsonrpc_request = self._build_jsonrpc_request(
#                 method="generate",
#                 params={
#                     "model": "llama3.2:3b",
#                     "prompt": prompt,
#                     "stream": False,
#                     "temperature": 0.3
#                 }
#             )
            
#             async with httpx.AsyncClient(timeout=60.0) as client:
#                 response = await client.post(
#                     self.llm_url,
#                     json=jsonrpc_request,
#                     headers=self.headers
#                 )
                
#                 if response.status_code == 200:
#                     data = response.json()
                    
#                     if "result" in data:
#                         result = data["result"]
#                         llm_response = result.get("response", "") if isinstance(result, dict) else str(result)
#                         print(f"✅ LLM Proxy response ({len(llm_response)} chars)")
#                         return llm_response
#                     elif "error" in data:
#                         print(f"❌ LLM Proxy error: {data['error']}")
#                         return None
#                     else:
#                         return str(data)
#                 else:
#                     print(f"❌ LLM Proxy error: {response.text}")
#                     return None
#         except Exception as e:
#             print(f"❌ Error calling LLM Proxy: {e}")
#             return None
    
#     async def send_to_a2a_gateway(self, agent_message: dict) -> dict:
#         """
#         Send message through A2A Gateway using JSON-RPC
#         For agent-to-agent communication
#         """
#         import httpx
        
#         try:
#             # Build JSON-RPC request
#             jsonrpc_request = self._build_jsonrpc_request(
#                 method="send_message",
#                 params=agent_message
#             )
            
#             async with httpx.AsyncClient(timeout=30.0) as client:
#                 response = await client.post(
#                     self.a2a_url,
#                     json=jsonrpc_request,
#                     headers=self.headers
#                 )
                
#                 if response.status_code in [200, 201]:
#                     try:
#                         result = response.json()
#                         if "result" in result:
#                             print(f"✅ A2A Gateway success")
#                             return result["result"]
#                         elif "error" in result:
#                             print(f"❌ A2A Gateway error: {result['error']}")
#                             return {"error": result["error"]}
#                         else:
#                             print(f"✅ A2A Gateway response received")
#                             return result
#                     except:
#                         print(f"✅ A2A Gateway response (non-JSON)")
#                         return {"status": "success"}
#                 else:
#                     print(f"❌ A2A Gateway error: {response.text}")
#                     return {"error": response.text}
#         except Exception as e:
#             print(f"❌ Error sending to A2A Gateway: {e}")
#             return {"error": str(e)}
    
#     async def check_archestra_health(self) -> bool:
#         """
#         Check if Archestra is online
#         """
#         import httpx
        
#         try:
#             async with httpx.AsyncClient(timeout=5.0) as client:
#                 response = await client.get(
#                     f"{ARCHESTRA_CONFIG['base_url']}/health",
#                     headers={"Authorization": f"Bearer {self.token}"}
#                 )
                
#                 if response.status_code == 200:
#                     print("✅ Archestra is online")
#                     return True
#                 else:
#                     print("⚠️ Archestra health check failed")
#                     return False
#         except Exception as e:
#             print(f"⚠️ Cannot reach Archestra: {e}")
#             return False

# # Create global instance
# archestra_gateway = ArchestraGateway()