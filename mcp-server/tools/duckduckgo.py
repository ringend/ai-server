from ddgs import DDGS

async def duckduckgo_full_search(query: str):
    results = {
        "answers": [],
        "news": [],
        "web": []
    }

    with DDGS() as ddgs:

        # Instant answers (weather, sports, conversions, facts, etc.)
        try:
            for a in ddgs.answers(query):
                results["answers"].append(a)
        except Exception:
            pass  # Some queries may not support answers()

        # News
        try:
            for n in ddgs.news(query, max_results=5):
                results["news"].append({
                    "title": n.get("title"),
                    "source": n.get("source"),
                    "date": n.get("date"),
                    "url": n.get("url")
                })
        except Exception:
            pass

        # Web results
        try:
            for r in ddgs.text(query, max_results=5):
                results["web"].append({
                    "title": r.get("title"),
                    "url": r.get("href"),
                    "snippet": r.get("body")
                })
        except Exception:
            pass

    # Format MCP response
    return {
        "content": [
            {
                "type": "json",
                "json": results
            }
        ]
    }


# ---------------------------------------------------------
# REQUIRED: MCP tool definition
# ---------------------------------------------------------
tool = {
    "name": "duckduckgo_full_search",
    "description": "Full DuckDuckGo search including instant answers, news, and web results.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        },
        "required": ["query"]
    },
    "handler": duckduckgo_full_search
}
