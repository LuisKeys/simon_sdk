from pathlib import Path

from simon.tools.tool import tool


@tool
def fs_read(path: str) -> str:
    """Read a text file and return its contents."""
    p = Path(path)
    if not p.exists():
        return f"Error: file not found: {path}"
    if not p.is_file():
        return f"Error: not a file: {path}"
    return p.read_text(encoding="utf-8", errors="ignore")


@tool
def fs_list(path: str) -> str:
    """List the contents of a directory."""
    p = Path(path)
    if not p.exists():
        return f"Error: path not found: {path}"
    if not p.is_dir():
        return f"Error: not a directory: {path}"
    entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name))
    lines = [f"{'dir ' if e.is_dir() else 'file'} {e.name}" for e in entries]
    return "\n".join(lines) if lines else "(empty)"


@tool
def fs_write(path: str, content: str) -> str:
    """Write content to a file, creating it if it doesn't exist."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} characters to {path}"
