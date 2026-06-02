import json
import urllib.parse
import urllib.request

from simon.tools.tool import tool

_MAX_BODY = 4000


@tool
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo and return top results."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception as exc:
        return f"Search error: {exc}"

    parts = []
    if data.get("AbstractText"):
        parts.append(data["AbstractText"])
    for r in data.get("RelatedTopics", [])[:5]:
        if isinstance(r, dict) and r.get("Text"):
            parts.append(r["Text"])
    return "\n\n".join(parts) if parts else "No results found."


@tool
def http_get(url: str) -> str:
    """Fetch a URL and return the response body (truncated to 4000 chars)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "simon-sdk/0.1"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        return f"HTTP error: {exc}"
    return body[:_MAX_BODY] + ("..." if len(body) > _MAX_BODY else "")
