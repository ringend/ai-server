# Configuration for the ai-backend server

import os

BASE_DIR = "/home/djr/ai-server/ai-backend"

class Config:
    # -----------------------------
    # LLM settings
    LLM_URL = "http://s1-aga.ringen.cloud:11435/api/chat"
    DEFAULT_MODEL = "phi4-optimized"

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

===========================
AVAILABLE TOOLS
===========================
You have access to the following tools:

duckduckgo_full_search:
    Full DuckDuckGo search including instant answers, news, and web results.
    Parameters:
        query: string

http_fetch:
    Fetch any URL and return text or binary content.
    Parameters:
        url: string
        timeout: number

html_extract:
    Parse HTML to extract text, links, cleaned HTML, or metadata.
    Parameters:
        html: string
        selector: string
        mode: text | links | html | metadata
        max_length: number

===========================
TOOL CALLING FORMAT
===========================
When you need to use a tool, respond ONLY with JSON:

{
  "tool": "<tool_name>",
  "arguments": {
      ... arguments ...
  }
}

Do NOT add commentary or markdown.

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

