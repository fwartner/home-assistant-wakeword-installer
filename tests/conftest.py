"""Shared fixtures for Wakeword Installer tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.wakeword_installer.const import DOMAIN, CONF_REPOSITORIES


@pytest.fixture
def mock_hass() -> MagicMock:
    """Create a mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.config_entries = MagicMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.config_entries.async_update_entry = MagicMock()
    hass.services = MagicMock()
    hass.services.async_register = MagicMock()
    hass.services.async_remove = MagicMock()
    hass.services.has_service = MagicMock(return_value=False)
    hass.async_add_executor_job = AsyncMock(side_effect=lambda fn, *a: fn(*a))
    return hass


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Create a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_REPOSITORIES: [
            {
                "repo_name": "test-repo",
                "repo_url": "https://github.com/test/wakewords",
                "selected_languages": ["en", "de"],
            }
        ]
    }
    entry.options = {}
    return entry


@pytest.fixture
def mock_empty_config_entry() -> MagicMock:
    """Create a mock config entry with no repositories."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.data = {CONF_REPOSITORIES: []}
    entry.options = {}
    return entry


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create a mock aiohttp session."""
    session = AsyncMock()
    session.closed = False
    return session


@pytest.fixture
def github_api_response() -> list[dict]:
    """Sample GitHub API response for repository contents."""
    return [
        {"name": "en", "type": "dir"},
        {"name": "de", "type": "dir"},
        {"name": "fr", "type": "dir"},
        {"name": "README.md", "type": "file"},
        {"name": ".gitignore", "type": "file"},
    ]
