import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from simon.tools.builtin import (
    datetime_now,
    fs_list,
    fs_read,
    fs_write,
    shell_run,
    http_get,
)


def test_fs_write_read_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "test.txt")
        result = fs_write(path=path, content="hello simon")
        assert "11" in result or "hello" in result.lower() or "Written" in result
        assert fs_read(path=path) == "hello simon"


def test_fs_read_missing():
    result = fs_read(path="/nonexistent/path/file.txt")
    assert "Error" in result


def test_fs_list():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "a.txt").write_text("x")
        (Path(tmp) / "subdir").mkdir()
        result = fs_list(path=tmp)
        assert "a.txt" in result
        assert "subdir" in result


def test_fs_list_missing():
    result = fs_list(path="/nonexistent/dir")
    assert "Error" in result


def test_datetime_now_is_valid_iso():
    result = datetime_now()
    parsed = datetime.fromisoformat(result)
    assert parsed.tzinfo is not None


def test_shell_run_echo():
    result = shell_run(command="echo hello")
    assert "hello" in result


def test_shell_run_timeout():
    result = shell_run(command="sleep 30")
    assert "timed out" in result.lower()


def test_http_get_mocked():
    fake_body = "A" * 5000
    with patch("urllib.request.urlopen") as mock_open:
        mock_resp = mock_open.return_value.__enter__.return_value
        mock_resp.read.return_value = fake_body.encode()
        result = http_get(url="http://example.com")
    assert len(result) == 4003  # 4000 chars + "..."
    assert result.endswith("...")
