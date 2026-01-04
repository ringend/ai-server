from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

async def html_extract(
    html: str,
    selector: Optional[str] = None,
    mode: str = "text",
    max_length: Optional[int] = 20000
) -> Dict[str, Any]:
    """
    HTML parsing tool for MCP.

    - html: raw HTML string to parse.
    - selector: optional CSS selector to narrow focus.
    - mode:
        - "text": main readable text content.
        - "links": list of links (text + href).
        - "html": cleaned inner HTML of selection/page.
        - "metadata": title, description, og: tags, etc.
    - max_length: optional truncation for large outputs.
    """

    soup = BeautifulSoup(html, "html.parser")

    # If a selector is provided, focus on that subset
    nodes = [soup]
    if selector:
        nodes = soup.select(selector)
        if not nodes:
            return {
                "content": [
                    {
                        "type": "json",
                        "json": {
                            "error": f"No elements matched selector '{selector}'"
                        },
                    }
                ]
            }

    def truncate(text: str) -> str:
        if max_length is not None and len(text) > max_length:
            return text[:max_length] + "\n\n[truncated]"
        return text

    if mode == "text":
        # Extract readable text
        texts: List[str] = []
        for node in nodes:
            # Get visible text; strip excessive whitespace
            text = " ".join(node.get_text(separator=" ", strip=True).split())
            if text:
                texts.append(text)

        full_text = "\n\n---\n\n".join(texts)
        full_text = truncate(full_text)

        return {
            "content": [
                {
                    "type": "text",
                    "text": full_text,
                }
            ]
        }

    elif mode == "links":
        links: List[Dict[str, Any]] = []
        for node in nodes:
            for a in node.find_all("a", href=True):
                text = " ".join(a.get_text(separator=" ", strip=True).split())
                href = a["href"]
                if text or href:
                    links.append(
                        {
                            "text": text,
                            "href": href,
                        }
                    )

        return {
            "content": [
                {
                    "type": "json",
                    "json": {
                        "links": links,
                    },
                }
            ]
        }

    elif mode == "html":
        # Return cleaned HTML for the selection or whole page
        fragments: List[str] = []
        for node in nodes:
            # inner HTML if element; otherwise whole document
            if getattr(node, "body", None):
                inner = str(node.body)
            else:
                inner = str(node)
            fragments.append(inner)

        joined = "\n\n<!-- --- -->\n\n".join(fragments)
        joined = truncate(joined)

        return {
            "content": [
                {
                    "type": "text",
                    "text": joined,
                }
            ]
        }

    elif mode == "metadata":
        # Extract basic metadata: title, description, og:*, etc.
        head = soup.head or soup

        def meta(name: str = None, property: str = None) -> Optional[str]:
            if name:
                tag = head.find("meta", attrs={"name": name})
                if tag and tag.get("content"):
                    return tag["content"]
            if property:
                tag = head.find("meta", attrs={"property": property})
                if tag and tag.get("content"):
                    return tag["content"]
            return None

        metadata = {
            "title": (head.title.string.strip() if head.title and head.title.string else None),
            "meta_description": meta("description"),
            "meta_keywords": meta("keywords"),
            "og_title": meta(property="og:title"),
            "og_description": meta(property="og:description"),
            "og_url": meta(property="og:url"),
            "og_site_name": meta(property="og:site_name"),
            "og_type": meta(property="og:type"),
        }

        return {
            "content": [
                {
                    "type": "json",
                    "json": metadata,
                }
            ]
        }

    else:
        return {
            "content": [
                {
                    "type": "json",
                    "json": {
                        "error": f"Unsupported mode '{mode}'. Use one of: text, links, html, metadata."
                    },
                }
            ]
        }


# ---------------------------------------------------------
# MCP tool definition
# ---------------------------------------------------------
tool = {
    "name": "html_extract",
    "description": "Parse HTML to extract text, links, cleaned HTML, or metadata.",
    "input_schema": {
        "type": "object",
        "properties": {
            "html": {"type": "string"},
            "selector": {"type": "string"},
            "mode": {
                "type": "string",
                "enum": ["text", "links", "html", "metadata"],
                "default": "text",
            },
            "max_length": {"type": "number"},
        },
        "required": ["html"],
    },
    "handler": html_extract,
}
