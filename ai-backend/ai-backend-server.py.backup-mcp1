# ==================================
# AI Backend Server

# Standard library
import os
import time
import json
import logging
import asyncio

# Third‑party libraries
import requests
import websockets
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from logging.handlers import RotatingFileHandler

# ======================================
# Load config variables from config/config.py
from config.config import config as cfg


# =======================================
# Logging Setup
os.makedirs(os.path.dirname(cfg.LOG_PATH), exist_ok=True)

handler = RotatingFileHandler(
    cfg.LOG_PATH,
    maxBytes=cfg.LOG_MAX_BYTES,
    backupCount=cfg.LOG_BACKUP_COUNT,
    encoding="utf-8"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[handler]
)

# ===================================
# Start FastAPI
app = FastAPI()

# ===================================
# CORS Handling
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to ["http://localhost:1313"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================================
# Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    client_ip = request.client.host
    method = request.method
    url = request.url.path

    logging.info(f"Incoming request: {client_ip} {method} {url}")

    response = await call_next(request)

    duration = (time.time() - start_time) * 1000
    status = response.status_code

    logging.info(
        f"Completed request: {client_ip} {method} {url} "
        f"Status={status} Duration={duration:.2f}ms"
    )

    return response


# ================================================
# Connection to MCP Server
class MCPClient:
    def __init__(self, url=cfg.MCP_URL):
        self.url = url
        self.ws = None
        self.request_id = 0

    async def connect(self):
        logging.info(f"Connecting to MCP server at {self.url} ...")
        self.ws = await websockets.connect(self.url)
        resp = await self.initialize()
        logging.info(f"MCP initialize response: {resp}")

    async def initialize(self):
        self.request_id += 1
        await self.ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "initialize",
            "params": {}
        }))
        return await self.ws.recv()

    async def call_tool(self, name, arguments):
        self.request_id += 1
        await self.ws.send(json.dumps({
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools.call",
            "params": {
                "name": name,
                "arguments": arguments
            }
        }))
        response = await self.ws.recv()
        return json.loads(response)


# Create a global MCP client instance
mcp_client = MCPClient()


# Startup event to connect MCP once
@app.on_event("startup")
async def startup_event():
    await mcp_client.connect()


# =====================================
# Chat Request Model
class ChatRequest(BaseModel):
    session_id: str
    message: str


# ======================================
# In-memory Conversation store
conversations = {}

SYSTEM_PROMPT = cfg.SYSTEM_PROMPT


# =====================================================
# Chat stt (voice) endpoint
@app.post("/stt")
async def stt(file: UploadFile = File(...)):
    try:
        # Forward audio file to Whisper STT server
        files = {
            "audio": (file.filename, await file.read(), file.content_type)
        }

        response = requests.post(cfg.STT_URL, files=files, timeout=60)

        if response.status_code != 200:
            logging.error(f"STT server error: {response.text}")
            raise HTTPException(status_code=500, detail="STT server error")

        data = response.json()
        return {"text": data.get("transcript", "")}

    except Exception as e:
        logging.error(f"STT error: {e}")
        raise HTTPException(status_code=500, detail="Failed to transcribe audio")


# ======================================================
# CHAT ENDPOINT (STREAMING)
@app.post("/chat")
async def chat(req: ChatRequest):

    session_id = req.session_id
    user_message = req.message

    logging.info(f"Chat request: session={session_id}, message={user_message[:80]}...")

    # Initialize conversation if new
    if session_id not in conversations:
        conversations[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # Append user message
    conversations[session_id].append({
        "role": "user",
        "content": user_message
    })

    # Build initial payload for Ollama
    payload = {
        "model": cfg.DEFAULT_MODEL,
        "messages": conversations[session_id],
        "tools": cfg.TOOLS,
        "stream": True
    }

    def stream_llm():
        assistant_reply = ""

        try:
            # First LLM call (may or may not request tools)
            with requests.post(cfg.LLM_URL, json=payload, stream=True) as r:
                r.raise_for_status()

                for line in r.iter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line.decode("utf-8"))
                    except Exception as e:
                        logging.error(f"Stream decode error: {e}")
                        continue

                    msg = data.get("message", {})

                    # -----------------------------
                    # TOOL CALL HANDLING
                    # -----------------------------
                    if msg.get("tool"):
                        tool_name = msg["tool"]["name"]
                        tool_args = msg["tool"]["arguments"]

                        logging.info(f"Tool call requested: {tool_name} {tool_args}")

                        # Call MCP tool (sync wrapper around async)
                        try:
                            tool_result = asyncio.run(
                                mcp_client.call_tool(tool_name, tool_args)
                            )
                        except RuntimeError:
                            # If an event loop is already running in this thread, use it
                            loop = asyncio.get_event_loop()
                            tool_result = loop.run_until_complete(
                                mcp_client.call_tool(tool_name, tool_args)
                            )

                        logging.info(f"Tool result for {tool_name}: {tool_result}")

                        # Append tool result to conversation
                        conversations[session_id].append({
                            "role": "tool",
                            "tool_name": tool_name,
                            "content": json.dumps(tool_result)
                        })

                        # Restart LLM with tool result included
                        next_payload = {
                            "model": cfg.DEFAULT_MODEL,
                            "messages": conversations[session_id],
                            "stream": True
                        }

                        with requests.post(cfg.LLM_URL, json=next_payload, stream=True) as r2:
                            r2.raise_for_status()
                            for line2 in r2.iter_lines():
                                if not line2:
                                    continue
                                try:
                                    data2 = json.loads(line2.decode("utf-8"))
                                except Exception as e:
                                    logging.error(f"Stream decode error (second pass): {e}")
                                    continue

                                token2 = data2.get("message", {}).get("content", "")
                                if token2:
                                    assistant_reply += token2
                                    yield token2

                        # After handling the tool call and second pass, end original stream
                        return

                    # -----------------------------
                    # NORMAL TEXT TOKEN
                    # -----------------------------
                    token = msg.get("content", "")
                    if token:
                        assistant_reply += token
                        yield token

        except Exception as e:
            logging.error(f"LLM streaming failed: {e}")
            yield f"[ERROR] {str(e)}"
            return

        # Save assistant reply
        conversations[session_id].append({
            "role": "assistant",
            "content": assistant_reply
        })

    return StreamingResponse(stream_llm(), media_type="text/plain")


# ======================================================
# HEALTH CHECK
@app.get("/health")
def health():
    logging.info("Health check called.")
    return {"status": "ok"}

