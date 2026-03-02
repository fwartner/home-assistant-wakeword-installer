"""Tests for the Wakeword Installer __init__ module."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.wakeword_installer import (
    DOMAIN,
    SERVICE_INSTALL_WAKEWORDS,
    SERVICE_LIST_INSTALLED,
    SERVICE_REFRESH_REPOSITORIES,
    SERVICE_REMOVE_REPOSITORY_WAKEWORDS,
    SERVICE_REMOVE_WAKEWORDS,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)


@pytest.mark.asyncio
class TestAsyncSetup:
    """Test async_setup."""

    async def test_returns_true(self, mock_hass: MagicMock) -> None:
        assert await async_setup(mock_hass, {}) is True


@pytest.mark.asyncio
class TestAsyncSetupEntry:
    """Test async_setup_entry."""

    async def test_registers_services(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        with patch("custom_components.wakeword_installer.RepositoryManager"):
            result = await async_setup_entry(mock_hass, mock_config_entry)

        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]

        # 5 services should be registered
        assert mock_hass.services.async_register.call_count == 5

        registered = [call.args[1] for call in mock_hass.services.async_register.call_args_list]
        assert SERVICE_INSTALL_WAKEWORDS in registered
        assert SERVICE_REMOVE_WAKEWORDS in registered
        assert SERVICE_REMOVE_REPOSITORY_WAKEWORDS in registered
        assert SERVICE_LIST_INSTALLED in registered
        assert SERVICE_REFRESH_REPOSITORIES in registered

    async def test_stores_entry_data(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        with patch("custom_components.wakeword_installer.RepositoryManager"):
            await async_setup_entry(mock_hass, mock_config_entry)

        assert mock_hass.data[DOMAIN][mock_config_entry.entry_id] == mock_config_entry.data

    async def test_forwards_platforms(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        with patch("custom_components.wakeword_installer.RepositoryManager"):
            await async_setup_entry(mock_hass, mock_config_entry)

        mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
            mock_config_entry, []
        )


@pytest.mark.asyncio
class TestAsyncUnloadEntry:
    """Test async_unload_entry."""

    async def test_successful_unload(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        # Setup first
        mock_hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_config_entry.data}

        result = await async_unload_entry(mock_hass, mock_config_entry)

        assert result is True
        assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]
        assert mock_hass.services.async_remove.call_count == 5

    async def test_failed_unload_keeps_data(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        mock_hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_config_entry.data}
        mock_hass.config_entries.async_unload_platforms = AsyncMock(return_value=False)

        result = await async_unload_entry(mock_hass, mock_config_entry)

        assert result is False
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
        mock_hass.services.async_remove.assert_not_called()


@pytest.mark.asyncio
class TestServiceCalls:
    """Test the service call handlers registered in async_setup_entry."""

    def _get_service_handler(self, mock_hass: MagicMock, service_name: str):
        """Find handler for a specific service from registered calls."""
        for c in mock_hass.services.async_register.call_args_list:
            if c.args[1] == service_name:
                return c.args[2]
        raise ValueError(f"Service {service_name} not registered")

    async def test_install_wakewords_all_repos(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        with patch("custom_components.wakeword_installer.RepositoryManager") as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.install_wakewords = AsyncMock()
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            await async_setup_entry(mock_hass, mock_config_entry)
            handler = self._get_service_handler(mock_hass, SERVICE_INSTALL_WAKEWORDS)

            call = MagicMock()
            call.data = {}
            await handler(call)

            mock_rm.install_wakewords.assert_called_once()
            mock_rm.close.assert_called()

    async def test_install_wakewords_specific_repo(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        with patch("custom_components.wakeword_installer.RepositoryManager") as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.install_wakewords = AsyncMock()
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            await async_setup_entry(mock_hass, mock_config_entry)
            handler = self._get_service_handler(mock_hass, SERVICE_INSTALL_WAKEWORDS)

            call = MagicMock()
            call.data = {"repository": "test-repo"}
            await handler(call)

            mock_rm.install_wakewords.assert_called_once()

    async def test_install_wakewords_wrong_repo_skips(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        with patch("custom_components.wakeword_installer.RepositoryManager") as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.install_wakewords = AsyncMock()
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            await async_setup_entry(mock_hass, mock_config_entry)
            handler = self._get_service_handler(mock_hass, SERVICE_INSTALL_WAKEWORDS)

            call = MagicMock()
            call.data = {"repository": "nonexistent-repo"}
            await handler(call)

            mock_rm.install_wakewords.assert_not_called()
            mock_rm.close.assert_called()

    async def test_remove_wakewords(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        with patch("custom_components.wakeword_installer.RepositoryManager") as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.remove_wakewords = AsyncMock()
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            await async_setup_entry(mock_hass, mock_config_entry)
            handler = self._get_service_handler(mock_hass, SERVICE_REMOVE_WAKEWORDS)

            call = MagicMock()
            call.data = {"repository": "test-repo", "languages": ["en"]}
            await handler(call)

            mock_rm.remove_wakewords.assert_called_once_with("test-repo", ["en"])
            mock_rm.close.assert_called()

    async def test_remove_repository_wakewords(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        with patch("custom_components.wakeword_installer.RepositoryManager") as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.remove_repository_wakewords = AsyncMock()
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            await async_setup_entry(mock_hass, mock_config_entry)
            handler = self._get_service_handler(mock_hass, SERVICE_REMOVE_REPOSITORY_WAKEWORDS)

            call = MagicMock()
            call.data = {"repository": "test-repo"}
            await handler(call)

            mock_rm.remove_repository_wakewords.assert_called_once_with("test-repo")

    async def test_list_installed(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        with patch("custom_components.wakeword_installer.RepositoryManager") as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.get_installed_wakewords = AsyncMock(return_value={})
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            await async_setup_entry(mock_hass, mock_config_entry)
            handler = self._get_service_handler(mock_hass, SERVICE_LIST_INSTALLED)

            call = MagicMock()
            call.data = {}
            await handler(call)

            mock_rm.get_installed_wakewords.assert_called_once()

    async def test_refresh_repositories(self, mock_hass: MagicMock, mock_config_entry: MagicMock) -> None:
        with patch("custom_components.wakeword_installer.RepositoryManager") as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.get_available_languages = AsyncMock(return_value=["en", "de"])
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            await async_setup_entry(mock_hass, mock_config_entry)
            handler = self._get_service_handler(mock_hass, SERVICE_REFRESH_REPOSITORIES)

            call = MagicMock()
            call.data = {}
            await handler(call)

            mock_rm.get_available_languages.assert_called_once()
