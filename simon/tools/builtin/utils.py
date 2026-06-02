from datetime import datetime, timezone

from simon.tools.tool import tool


@tool
def datetime_now() -> str:
    """Return the current date and time in ISO 8601 format (UTC)."""
    return datetime.now(tz=timezone.utc).isoformat()
