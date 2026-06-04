from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from simon.agent.agent import _enabled_knowledge_dirs


def _mock_settings(**flags):
    defaults = dict(
        enable_dir_documents=False,
        enable_dir_downloads=False,
        enable_dir_pictures=False,
        enable_dir_desktop=False,
    )
    defaults.update(flags)
    return SimpleNamespace(**defaults)


def test_default_enabled_dirs():
    mock = _mock_settings(enable_dir_documents=True, enable_dir_downloads=True)
    with patch("simon.agent.agent.settings", mock):
        dirs = _enabled_knowledge_dirs()
    assert Path.home() / "Documents" in dirs
    assert Path.home() / "Downloads" in dirs
    assert len(dirs) == 2


def test_all_disabled_returns_empty():
    mock = _mock_settings()
    with patch("simon.agent.agent.settings", mock):
        dirs = _enabled_knowledge_dirs()
    assert dirs == []


def test_only_documents_enabled():
    mock = _mock_settings(enable_dir_documents=True)
    with patch("simon.agent.agent.settings", mock):
        dirs = _enabled_knowledge_dirs()
    assert dirs == [Path.home() / "Documents"]


def test_pictures_and_desktop_enabled():
    mock = _mock_settings(enable_dir_pictures=True, enable_dir_desktop=True)
    with patch("simon.agent.agent.settings", mock):
        dirs = _enabled_knowledge_dirs()
    assert Path.home() / "Pictures" in dirs
    assert Path.home() / "Desktop" in dirs
    assert len(dirs) == 2


def test_all_enabled():
    mock = _mock_settings(
        enable_dir_documents=True,
        enable_dir_downloads=True,
        enable_dir_pictures=True,
        enable_dir_desktop=True,
    )
    with patch("simon.agent.agent.settings", mock):
        dirs = _enabled_knowledge_dirs()
    assert len(dirs) == 4
