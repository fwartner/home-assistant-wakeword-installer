"""Config flow for Wakeword Installer integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_REPOSITORIES, CONF_REPO_URL, CONF_REPO_NAME, CONF_SELECTED_LANGUAGES
from .repository_manager import RepositoryManager

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_REPO_NAME): str,
        vol.Required(CONF_REPO_URL): str,
    }
)


class WakewordInstallerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Wakeword Installer."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.repositories = []
        self.current_repo = {}
        self.available_languages = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            # Validate repository URL and fetch available languages
            repo_manager = RepositoryManager(self.hass)
            languages = await repo_manager.get_available_languages(user_input[CONF_REPO_URL])
            
            if not languages:
                errors["base"] = "no_languages_found"
            else:
                self.current_repo = {
                    CONF_REPO_NAME: user_input[CONF_REPO_NAME],
                    CONF_REPO_URL: user_input[CONF_REPO_URL],
                }
                self.available_languages = languages
                return await self.async_step_select_languages()

        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidRepo:
            errors["base"] = "invalid_repo"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_select_languages(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle language selection step."""
        if user_input is None:
            language_schema = vol.Schema({
                vol.Required(CONF_SELECTED_LANGUAGES, default=self.available_languages): 
                cv.multi_select(self.available_languages)
            })
            return self.async_show_form(
                step_id="select_languages", 
                data_schema=language_schema,
                description_placeholders={
                    "repo_name": self.current_repo[CONF_REPO_NAME],
                    "available_languages": ", ".join(self.available_languages)
                }
            )

        # Add the repository with selected languages
        repo_config = {
            **self.current_repo,
            CONF_SELECTED_LANGUAGES: user_input[CONF_SELECTED_LANGUAGES]
        }
        self.repositories.append(repo_config)

        return await self.async_step_add_more()

    async def async_step_add_more(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask if user wants to add more repositories."""
        if user_input is None:
            return self.async_show_form(
                step_id="add_more",
                data_schema=vol.Schema({
                    vol.Required("add_another", default=False): bool
                }),
                description_placeholders={
                    "current_repos": "\n".join([f"• {repo[CONF_REPO_NAME]}" for repo in self.repositories])
                }
            )

        if user_input["add_another"]:
            return await self.async_step_user()

        # Create the config entry
        return self.async_create_entry(
            title="Wakeword Installer",
            data={CONF_REPOSITORIES: self.repositories}
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> WakewordInstallerOptionsFlow:
        """Get the options flow for this handler."""
        return WakewordInstallerOptionsFlow(config_entry)


class WakewordInstallerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Wakeword Installer."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.repositories = config_entry.data.get(CONF_REPOSITORIES, [])

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return await self.async_step_manage_repos()

    async def async_step_manage_repos(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage repositories."""
        if user_input is None:
            repo_list = [f"{repo[CONF_REPO_NAME]} ({repo[CONF_REPO_URL]})" for repo in self.repositories]
            
            if not repo_list:
                repo_list = ["No repositories configured"]

            return self.async_show_form(
                step_id="manage_repos",
                data_schema=vol.Schema({
                    vol.Optional("action"): vol.In(["add", "remove", "install", "done"]),
                    vol.Optional("repo_to_remove"): vol.In(repo_list) if len(self.repositories) > 0 else str,
                }),
                description_placeholders={
                    "repo_list": "\n".join([f"• {repo}" for repo in repo_list])
                }
            )

        action = user_input.get("action")
        
        if action == "add":
            return await self.async_step_add_repo()
        elif action == "remove":
            return await self.async_step_remove_repo(user_input)
        elif action == "install":
            return await self.async_step_install_wakewords()
        else:
            return self.async_create_entry(title="", data={})

    async def async_step_add_repo(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new repository."""
        if user_input is None:
            return self.async_show_form(
                step_id="add_repo",
                data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}
        try:
            repo_manager = RepositoryManager(self.hass)
            languages = await repo_manager.get_available_languages(user_input[CONF_REPO_URL])
            
            if languages:
                new_repo = {
                    CONF_REPO_NAME: user_input[CONF_REPO_NAME],
                    CONF_REPO_URL: user_input[CONF_REPO_URL],
                    CONF_SELECTED_LANGUAGES: languages  # Select all by default
                }
                self.repositories.append(new_repo)
                
                # Update config entry
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={CONF_REPOSITORIES: self.repositories}
                )
            else:
                errors["base"] = "no_languages_found"

        except Exception:
            errors["base"] = "unknown"

        if errors:
            return self.async_show_form(
                step_id="add_repo",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors
            )

        return await self.async_step_manage_repos()

    async def async_step_remove_repo(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Remove a repository."""
        repo_to_remove = user_input.get("repo_to_remove")
        if repo_to_remove and repo_to_remove != "No repositories configured":
            # Extract repo name from the display string
            repo_name = repo_to_remove.split(" (")[0]
            
            # Remove all wakeword files associated with this repository
            try:
                repo_manager = RepositoryManager(self.hass)
                await repo_manager.remove_repository_wakewords(repo_name)
                await repo_manager.close()
                _LOGGER.info(f"Removed all wakeword files for repository: {repo_name}")
            except Exception as e:
                _LOGGER.error(f"Failed to remove wakeword files for {repo_name}: {e}")
            
            # Remove repository from configuration
            self.repositories = [repo for repo in self.repositories if repo[CONF_REPO_NAME] != repo_name]
            
            # Update config entry
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={CONF_REPOSITORIES: self.repositories}
            )

        return await self.async_step_manage_repos()

    async def async_step_install_wakewords(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Install wakewords from repositories."""
        repo_manager = RepositoryManager(self.hass)
        
        for repo in self.repositories:
            try:
                await repo_manager.install_wakewords(
                    repo[CONF_REPO_URL],
                    repo[CONF_SELECTED_LANGUAGES],
                    repo[CONF_REPO_NAME]
                )
            except Exception as e:
                _LOGGER.error(f"Failed to install wakewords from {repo[CONF_REPO_NAME]}: {e}")

        return self.async_show_form(
            step_id="install_complete",
            data_schema=vol.Schema({}),
            description_placeholders={
                "message": "Wakewords have been installed successfully!"
            }
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidRepo(HomeAssistantError):
    """Error to indicate there is invalid repository."""