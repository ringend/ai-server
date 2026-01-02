import httpx
import base64
from typing import Optional

async def http_fetch(url: str, timeout: Optional[float] = 10.0):
    """
    General-purpose HTTP fetch tool.
    - Returns text for HTML, JSON, XML, plaintext.
    - Returns base64 for binary (images, PDFs, etc.).
    - Follows redirects.
    - Safe user-agent.
    """

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=timeout,
        headers={
            "User-Agent": "MCP-HTTP-Fetch/1.0 (+https://example.com)"
        }
    ) as client:
        response = await client.get(url)

    content_type = response.headers.get("content-type", "").lower()

    # Decide if content is binary
    is_binary = any(
        binary_type in content_type
        for binary_type in [
            "image/",
            "application/pdf",
            "application/octet-stream",
            "application/zip",
            "audio/",
            "video/"
        ]
    )

    if is_binary:
        encoded = base64.b64encode(response.content).decode("utf-8")
        body = {
            "type": "binary",
            "encoding": "base64",
            "content": encoded
        }
    else:
        # Try to decode as text
        try:
            text = response.text
        except UnicodeDecodeError:
            # Fallback to base64 if decoding fails
            encoded = base64.b64encode(response.content).decode("utf-8")
            body = {
                "type": "binary",
                "encoding": "base64",
                "content": encoded
            }
        else:
            body = {
                "type": "text",
                "content": text
            }

    return {
        "content": [
            {
                "type": "json",
                "json": {
                    "url": url,
                    "status": response.status_code,
                    "headers": dict(response.headers),
                    "body": body
                }
            }
        ]
    }


# ---------------------------------------------------------
# MCP tool definition
# ---------------------------------------------------------
tool = {
    "name": "http_fetch",
    "description": "Fetch any URL and return text or binary content.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "timeout": {"type": "number"}
        },
        "required": ["url"]
    },
    "handler": http_fetch
}
