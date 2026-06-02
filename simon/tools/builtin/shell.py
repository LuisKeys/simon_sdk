import subprocess

from simon.tools.tool import tool


@tool
def shell_run(command: str) -> str:
    """Run a shell command and return its output (stdout + stderr)."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout + result.stderr
        return output.strip() if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 10 seconds"
    except Exception as exc:
        return f"Error: {exc}"
