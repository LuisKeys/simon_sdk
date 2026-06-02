import urllib.request

from simon.config.settings import settings
from simon.tools.tool import tool

_MAX_BODY = 4000


@tool
def web_search(query: str) -> str:
    """Search the web using OpenAI's built-in web search and return results."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install openai package to use web_search.") from exc

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        tools=[{"type": "web_search_preview"}],
        instructions="You are a web search assistant. Return a concise summary of the top results (3-5 bullet points max). No code examples, no headers, no lengthy explanations.",
        input=query,
    )
    return response.output_text or "No results found."


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
