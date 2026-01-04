# Configuration for the ai-backend server

import os

BASE_DIR = "/home/djr/ai-server/ai-backend"

class Config:
    # -----------------------------
    # LLM settings
    LLM_URL = "http://localhost:11434/api/chat"
    DEFAULT_MODEL = "llama3.1:8b"

    # -----------------------------
    # Logging settings
    LOG_PATH = os.path.join(BASE_DIR, "logs", "backend.log")
    LOG_MAX_BYTES = 10 * 1024 * 1024   # 10 MB
    LOG_BACKUP_COUNT = 7

    # -----------------------------
    # MCP settings
    MCP_URL = "ws://localhost:5002/mcp"

    # -----------------------------
    # stt settings
    STT_URL = "http://localhost:8001/stt"


    # -----------------------------
    # System Prompt
    SYSTEM_PROMPT = """
You are the Ringen Cloud AI Assistant. Your purpose is to answer questions and provide insights to questions asked.
=============
GUARDRAILS
=============
1. Moral and Safety Boundaries
   - Never encourage, endorse, or assist in any action that is harmful, abusive, violent, unlawful, or immoral.
   - If a user expresses intent to harm themselves or others, respond with pastoral compassion, remind them that you cannot provide crisis support, and encourage them to seek immediate help from trusted people, pastors, or local authorities.
   - Do not provide instructions, advice, or strategies related to self-harm, violence, illegal activity, or any behavior that contradicts Christian moral teaching.
   - If asked about committing a sin or immoral act, respond with Scripture-based correction and guidance toward repentance, wisdom, and righteousness.
   - Use Christian morals in respond to all questions and tasks.
"""

    # -----------------------------
    # Tool definitions for LLM
    # -----------------------------
    TOOLS = [
        {
            "name": "duckduckgo_full_search",
            "description": "Full DuckDuckGo search including instant answers, news, and web results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "http_fetch",
            "description": "Fetch any URL and return text or binary content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "timeout": {"type": "number"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "html_extract",
            "description": "Parse HTML to extract text, links, cleaned HTML, or metadata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "html": {"type": "string"},
                    "selector": {"type": "string"},
                    "mode": {
                       "type": "string",
                       "enum": ["text", "links", "html", "metadata"]
                    },
                    "max_length": {"type": "number"}
                },
                "required": ["html"]
            }
        }
    ]

config = Config()

