"""Tests for the Wakeword Installer config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.config_entries import ConfigEntry

from custom_components.wakeword_installer.config_flow import (
    WakewordInstallerConfigFlow,
    WakewordInstallerOptionsFlow,
)
from custom_components.wakeword_installer.const import (
    CONF_REPO_NAME,
    CONF_REPO_URL,
    CONF_REPOSITORIES,
    CONF_SELECTED_LANGUAGES,
    DOMAIN,
)


# --- ConfigFlow tests ---


@pytest.mark.asyncio
class TestConfigFlowUser:
    """Test the user step of the config flow."""

    async def test_show_form_on_none_input(self) -> None:
        flow = WakewordInstallerConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_user(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "user"

    async def test_valid_repo_proceeds_to_language_selection(self) -> None:
        flow = WakewordInstallerConfigFlow()
        flow.hass = MagicMock()

        with patch(
            "custom_components.wakeword_installer.config_flow.RepositoryManager"
        ) as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.get_available_languages = AsyncMock(return_value=["en", "de", "fr"])
            mock_rm._extract_repo_name = MagicMock(return_value="wakewords")
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            result = await flow.async_step_user(
                user_input={
                    CONF_REPO_URL: "https://github.com/test/wakewords",
                }
            )

            mock_rm.close.assert_called_once()

        assert result["type"] == "form"
        assert result["step_id"] == "select_languages"
        # Verify repo name was auto-extracted, not user-provided
        assert flow.current_repo[CONF_REPO_NAME] == "wakewords"

    async def test_empty_languages_shows_error(self) -> None:
        flow = WakewordInstallerConfigFlow()
        flow.hass = MagicMock()

        with patch(
            "custom_components.wakeword_installer.config_flow.RepositoryManager"
        ) as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.get_available_languages = AsyncMock(return_value=[])
            mock_rm._extract_repo_name = MagicMock(return_value="wakewords")
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            result = await flow.async_step_user(
                user_input={
                    CONF_REPO_URL: "https://github.com/test/wakewords",
                }
            )

            mock_rm.close.assert_called_once()

        assert result["type"] == "form"
        assert result["errors"]["base"] == "no_languages_found"

    async def test_exception_shows_unknown_error(self) -> None:
        flow = WakewordInstallerConfigFlow()
        flow.hass = MagicMock()

        with patch(
            "custom_components.wakeword_installer.config_flow.RepositoryManager"
        ) as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm._extract_repo_name = MagicMock(return_value="wakewords")
            mock_rm.get_available_languages = AsyncMock(side_effect=Exception("boom"))
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            result = await flow.async_step_user(
                user_input={
                    CONF_REPO_URL: "https://github.com/test/wakewords",
                }
            )

            mock_rm.close.assert_called_once()

        assert result["type"] == "form"
        assert result["errors"]["base"] == "unknown"


@pytest.mark.asyncio
class TestConfigFlowSelectLanguages:
    """Test the language selection step."""

    async def test_show_form_on_none_input(self) -> None:
        flow = WakewordInstallerConfigFlow()
        flow.hass = MagicMock()
        flow.current_repo = {CONF_REPO_NAME: "test", CONF_REPO_URL: "https://github.com/t/r"}
        flow.available_languages = ["en", "de"]

        result = await flow.async_step_select_languages(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "select_languages"

    async def test_selected_languages_stored(self) -> None:
        flow = WakewordInstallerConfigFlow()
        flow.hass = MagicMock()
        flow.current_repo = {CONF_REPO_NAME: "test", CONF_REPO_URL: "https://github.com/t/r"}
        flow.available_languages = ["en", "de", "fr"]

        result = await flow.async_step_select_languages(
            user_input={CONF_SELECTED_LANGUAGES: ["en", "de"]}
        )

        # Should proceed to add_more step
        assert result["type"] == "form"
        assert result["step_id"] == "add_more"
        assert len(flow.repositories) == 1
        assert flow.repositories[0][CONF_SELECTED_LANGUAGES] == ["en", "de"]


@pytest.mark.asyncio
class TestConfigFlowAddMore:
    """Test the add_more step."""

    async def test_show_form_on_none_input(self) -> None:
        flow = WakewordInstallerConfigFlow()
        flow.hass = MagicMock()
        flow.repositories = [{CONF_REPO_NAME: "test"}]

        result = await flow.async_step_add_more(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "add_more"

    async def test_done_creates_entry(self) -> None:
        flow = WakewordInstallerConfigFlow()
        flow.hass = MagicMock()
        flow.context = {}
        flow.repositories = [
            {
                CONF_REPO_NAME: "test",
                CONF_REPO_URL: "https://github.com/t/r",
                CONF_SELECTED_LANGUAGES: ["en"],
            }
        ]

        # Mock async_set_unique_id and _abort_if_unique_id_configured
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        result = await flow.async_step_add_more(user_input={"add_another": False})

        assert result["type"] == "create_entry"
        assert result["title"] == "Wakeword Installer"
        assert result["data"][CONF_REPOSITORIES] == flow.repositories
        flow.async_set_unique_id.assert_called_once_with(DOMAIN)
        flow._abort_if_unique_id_configured.assert_called_once()

    async def test_add_another_returns_to_user_step(self) -> None:
        flow = WakewordInstallerConfigFlow()
        flow.hass = MagicMock()
        flow.repositories = [{CONF_REPO_NAME: "test"}]

        result = await flow.async_step_add_more(user_input={"add_another": True})

        assert result["type"] == "form"
        assert result["step_id"] == "user"


# --- OptionsFlow tests ---


@pytest.mark.asyncio
class TestOptionsFlowInit:
    """Test the OptionsFlow initialization.

    This tests the fix for Issue #2 -- modern HA (2025.12+) makes config_entry
    a read-only property on OptionsFlow. The flow must NOT accept config_entry
    in __init__; it accesses self.config_entry set by the framework.
    """

    async def test_init_reads_config_entry(self) -> None:
        """Verify OptionsFlow can be created without arguments (Issue #2 fix)."""
        flow = WakewordInstallerOptionsFlow()
        # Set config_entry as the framework would
        flow._config_entry = MagicMock(spec=ConfigEntry)
        flow._config_entry.data = {
            CONF_REPOSITORIES: [
                {CONF_REPO_NAME: "repo1", CONF_REPO_URL: "https://github.com/t/r", CONF_SELECTED_LANGUAGES: ["en"]}
            ]
        }
        # Patch config_entry property to return our mock
        type(flow).config_entry = property(lambda self: self._config_entry)

        result = await flow.async_step_init(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "manage_repos"
        assert len(flow.repositories) == 1

    async def test_no_init_args_required(self) -> None:
        """Ensure WakewordInstallerOptionsFlow() takes no arguments (Issue #2)."""
        # This would raise TypeError if __init__ still required config_entry
        flow = WakewordInstallerOptionsFlow()
        assert flow is not None


@pytest.mark.asyncio
class TestOptionsFlowManageRepos:
    """Test manage_repos step."""

    async def test_show_form_on_none_input(self) -> None:
        flow = WakewordInstallerOptionsFlow()
        flow.repositories = [
            {CONF_REPO_NAME: "repo1", CONF_REPO_URL: "https://github.com/t/r"}
        ]

        result = await flow.async_step_manage_repos(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "manage_repos"

    async def test_empty_repos_shows_placeholder(self) -> None:
        flow = WakewordInstallerOptionsFlow()
        flow.repositories = []

        result = await flow.async_step_manage_repos(user_input=None)

        assert result["type"] == "form"

    async def test_done_action_creates_entry(self) -> None:
        flow = WakewordInstallerOptionsFlow()
        flow.repositories = []

        result = await flow.async_step_manage_repos(user_input={"action": "done"})

        assert result["type"] == "create_entry"


@pytest.mark.asyncio
class TestOptionsFlowAddRepo:
    """Test add_repo step."""

    async def test_show_form_on_none_input(self) -> None:
        flow = WakewordInstallerOptionsFlow()

        result = await flow.async_step_add_repo(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "add_repo"

    async def test_successful_add(self) -> None:
        flow = WakewordInstallerOptionsFlow()
        flow.hass = MagicMock()
        flow.repositories = []
        flow._config_entry = MagicMock()
        type(flow).config_entry = property(lambda self: self._config_entry)

        with patch(
            "custom_components.wakeword_installer.config_flow.RepositoryManager"
        ) as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.get_available_languages = AsyncMock(return_value=["en", "de"])
            mock_rm._extract_repo_name = MagicMock(return_value="new-repo")
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            result = await flow.async_step_add_repo(
                user_input={
                    CONF_REPO_URL: "https://github.com/t/new-repo",
                }
            )

            mock_rm.close.assert_called_once()

        assert result["type"] == "form"
        assert result["step_id"] == "manage_repos"
        assert len(flow.repositories) == 1
        assert flow.repositories[0][CONF_REPO_NAME] == "new-repo"


@pytest.mark.asyncio
class TestOptionsFlowRemoveRepo:
    """Test remove_repo step."""

    async def test_remove_existing_repo(self) -> None:
        flow = WakewordInstallerOptionsFlow()
        flow.hass = MagicMock()
        flow.repositories = [
            {CONF_REPO_NAME: "repo1", CONF_REPO_URL: "https://github.com/t/r1"},
            {CONF_REPO_NAME: "repo2", CONF_REPO_URL: "https://github.com/t/r2"},
        ]
        flow._config_entry = MagicMock()
        type(flow).config_entry = property(lambda self: self._config_entry)

        with patch(
            "custom_components.wakeword_installer.config_flow.RepositoryManager"
        ) as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.remove_repository_wakewords = AsyncMock()
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            result = await flow.async_step_remove_repo(
                user_input={"repo_to_remove": "repo1 (https://github.com/t/r1)"}
            )

            mock_rm.close.assert_called_once()

        assert result["type"] == "form"
        assert result["step_id"] == "manage_repos"
        assert len(flow.repositories) == 1
        assert flow.repositories[0][CONF_REPO_NAME] == "repo2"


@pytest.mark.asyncio
class TestOptionsFlowInstallWakewords:
    """Test install_wakewords step."""

    async def test_install_closes_session(self) -> None:
        flow = WakewordInstallerOptionsFlow()
        flow.hass = MagicMock()
        flow.repositories = [
            {
                CONF_REPO_NAME: "test-repo",
                CONF_REPO_URL: "https://github.com/t/r",
                CONF_SELECTED_LANGUAGES: ["en"],
            }
        ]

        with patch(
            "custom_components.wakeword_installer.config_flow.RepositoryManager"
        ) as mock_rm_cls:
            mock_rm = MagicMock()
            mock_rm.install_wakewords = AsyncMock()
            mock_rm.close = AsyncMock()
            mock_rm_cls.return_value = mock_rm

            result = await flow.async_step_install_wakewords()

            mock_rm.install_wakewords.assert_called_once()
            mock_rm.close.assert_called_once()

        assert result["type"] == "form"
        assert result["step_id"] == "install_complete"
