import token
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File, HTTPException
import requests
import logging
import os
import time
import json
import asyncio
import websockets
from logging.handlers import RotatingFileHandler
#Test 1

# Load config variables
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
# MCP Tool Call
async def call_mcp_tool(name, arguments):
    try:
        async with websockets.connect(cfg.MCP_URL) as ws:
            await ws.send(json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools.call",
                "params": {
                    "name": name,
                    "arguments": arguments
                }
            }))
            response = await ws.recv()
            data = json.loads(response)
            return data.get("result", {})
    except Exception as e:
        logging.error(f"MCP tool call failed: {e}")
        return {"error": str(e)}


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

    # Build payload for Ollama
    payload = {
        "model": cfg.DEFAULT_MODEL,
        "messages": conversations[session_id],
        "stream": True
    }

    def stream_llm():
        assistant_reply = ""

        try:
            with requests.post(cfg.LLM_URL, json=payload, stream=True) as r:
                r.raise_for_status()

                for line in r.iter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line.decode("utf-8"))

                        token = data.get("message", {}).get("content", "")
                        assistant_reply += token
                        
                        # === MCP TOOL CALL DETECTION ===
                        try:
                            clean = assistant_reply.strip()

                            # Remove Markdown fences if present
                            if clean.startswith("```"):
                                clean = clean.split("```", 1)[1].strip()
                                if clean.endswith("```"):
                                    clean = clean.rsplit("```", 1)[0].strip()

                            parsed = json.loads(clean)

                            if isinstance(parsed, dict) and "tool" in parsed:
                                tool_name = parsed["tool"]
                                tool_args = parsed.get("arguments", {}) 
                                # Call MCP tool
                                result = asyncio.run(call_mcp_tool(tool_name, tool_args))

                                # Add tool result to conversation
                                conversations[session_id].append({
                                    "role": "tool",
                                    "content": json.dumps(result)
                                })

                                # Restart LLM with tool result
                                followup_payload = {
                                    "model": cfg.DEFAULT_MODEL,
                                    "messages": conversations[session_id],
                                    "stream": True
                                }   
                                with requests.post(cfg.LLM_URL, json=followup_payload, stream=True) as r2:
                                    for line2 in r2.iter_lines():
                                        if not line2:
                                            continue
                                        data2 = json.loads(line2.decode("utf-8"))
                                        token2 = data2.get("message", {}).get("content", "")
                                        yield token2
                                return
                        except Exception:
                            pass

                        # Normal streaming
                        yield token     

                    except Exception as e:
                        logging.error(f"Stream decode error: {e}")
                        continue

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
