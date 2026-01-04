from fastapi import FastAPI, WebSocket
import json
import importlib
import pkgutil
import traceback
import inspect

app = FastAPI()

# ---------------------------------------------------------
# Load tools dynamically from tools/ directory
# ---------------------------------------------------------
def load_tools():
    tools = {}
    for module_info in pkgutil.iter_modules(['tools']):
        module = importlib.import_module(f"tools.{module_info.name}")
        if hasattr(module, "tool"):
            tools[module.tool["name"]] = module.tool
    return tools

TOOLS = load_tools()

# ---------------------------------------------------------
# Execute a tool (async‑safe)
# ---------------------------------------------------------
async def call_tool(name, arguments):
    tool = TOOLS.get(name)
    if not tool:
        return {"error": f"Tool '{name}' not found"}

    handler = tool["handler"]

    try:
        # If handler is async, await it
        if inspect.iscoroutinefunction(handler):
            return await handler(**arguments)

        # Otherwise call it normally
        return handler(**arguments)

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

# ---------------------------------------------------------
# WebSocket MCP endpoint
# ---------------------------------------------------------
@app.websocket("/mcp")
async def mcp_socket(ws: WebSocket):
    await ws.accept()

    while True:
        message = await ws.receive_text()
        request = json.loads(message)

        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        # initialize
        if method == "initialize":
            await ws.send_json({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "serverInfo": {
                        "name": "websocket-mcp-server",
                        "version": "0.1.0"
                    },
                    "capabilities": {
                        "tools": True
                    }
                }
            })
            continue

        # tools.list
        if method == "tools.list":
            await ws.send_json({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": t["name"],
                            "description": t["description"],
                            "inputSchema": t["input_schema"]
                        }
                        for t in TOOLS.values()
                    ]
                }
            })
            continue

        # tools.call
        if method == "tools.call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            result = await call_tool(name, arguments)

            await ws.send_json({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            })
            continue

        # unknown method
        await ws.send_json({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"message": f"Unknown method: {method}"}
        })

