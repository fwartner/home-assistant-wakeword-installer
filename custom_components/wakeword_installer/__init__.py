"""The Wakeword Installer integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_REPOSITORIES, CONF_REPO_NAME
from .repository_manager import RepositoryManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = []

SERVICE_INSTALL_WAKEWORDS = "install_wakewords"
SERVICE_REMOVE_WAKEWORDS = "remove_wakewords"
SERVICE_REMOVE_REPOSITORY_WAKEWORDS = "remove_repository_wakewords"
SERVICE_LIST_INSTALLED = "list_installed"
SERVICE_REFRESH_REPOSITORIES = "refresh_repositories"

SERVICE_INSTALL_SCHEMA = vol.Schema({
    vol.Optional("repository"): cv.string,
    vol.Optional("languages"): vol.All(cv.ensure_list, [cv.string]),
})

SERVICE_REMOVE_SCHEMA = vol.Schema({
    vol.Required("repository"): cv.string,
    vol.Required("languages"): vol.All(cv.ensure_list, [cv.string]),
})

SERVICE_REMOVE_REPOSITORY_SCHEMA = vol.Schema({
    vol.Required("repository"): cv.string,
})


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Wakeword Installer component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Wakeword Installer from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Register services
    async def install_wakewords_service(call: ServiceCall) -> None:
        """Handle install wakewords service call."""
        repo_manager = RepositoryManager(hass)
        try:
            repositories = entry.data.get(CONF_REPOSITORIES, [])
            target_repo = call.data.get("repository")
            target_languages = call.data.get("languages")
            
            for repo in repositories:
                if target_repo and repo[CONF_REPO_NAME] != target_repo:
                    continue
                    
                languages = target_languages or repo.get("selected_languages", [])
                await repo_manager.install_wakewords(repo["repo_url"], languages, repo[CONF_REPO_NAME])
                
        except Exception as e:
            _LOGGER.error(f"Failed to install wakewords: {e}")
        finally:
            await repo_manager.close()

    async def remove_wakewords_service(call: ServiceCall) -> None:
        """Handle remove wakewords service call."""
        repo_manager = RepositoryManager(hass)
        try:
            repo_name = call.data["repository"]
            languages = call.data["languages"]
            await repo_manager.remove_wakewords(repo_name, languages)
        except Exception as e:
            _LOGGER.error(f"Failed to remove wakewords: {e}")
        finally:
            await repo_manager.close()

    async def remove_repository_wakewords_service(call: ServiceCall) -> None:
        """Handle remove repository wakewords service call."""
        repo_manager = RepositoryManager(hass)
        try:
            repo_name = call.data["repository"]
            await repo_manager.remove_repository_wakewords(repo_name)
        except Exception as e:
            _LOGGER.error(f"Failed to remove repository wakewords: {e}")
        finally:
            await repo_manager.close()

    async def list_installed_service(call: ServiceCall) -> None:
        """Handle list installed wakewords service call."""
        repo_manager = RepositoryManager(hass)
        try:
            installed = await repo_manager.get_installed_wakewords()
            _LOGGER.info(f"Installed wakewords: {installed}")
        except Exception as e:
            _LOGGER.error(f"Failed to list installed wakewords: {e}")
        finally:
            await repo_manager.close()

    async def refresh_repositories_service(call: ServiceCall) -> None:
        """Handle refresh repositories service call."""
        repo_manager = RepositoryManager(hass)
        try:
            repositories = entry.data.get(CONF_REPOSITORIES, [])
            for repo in repositories:
                languages = await repo_manager.get_available_languages(repo["repo_url"])
                _LOGGER.info(f"Available languages for {repo[CONF_REPO_NAME]}: {languages}")
        except Exception as e:
            _LOGGER.error(f"Failed to refresh repositories: {e}")
        finally:
            await repo_manager.close()

    # Register all services
    hass.services.async_register(
        DOMAIN, SERVICE_INSTALL_WAKEWORDS, install_wakewords_service, schema=SERVICE_INSTALL_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REMOVE_WAKEWORDS, remove_wakewords_service, schema=SERVICE_REMOVE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REMOVE_REPOSITORY_WAKEWORDS, remove_repository_wakewords_service, schema=SERVICE_REMOVE_REPOSITORY_SCHEMA
    )
    hass.services.async_register(DOMAIN, SERVICE_LIST_INSTALLED, list_installed_service)
    hass.services.async_register(DOMAIN, SERVICE_REFRESH_REPOSITORIES, refresh_repositories_service)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Remove services
        hass.services.async_remove(DOMAIN, SERVICE_INSTALL_WAKEWORDS)
        hass.services.async_remove(DOMAIN, SERVICE_REMOVE_WAKEWORDS)
        hass.services.async_remove(DOMAIN, SERVICE_REMOVE_REPOSITORY_WAKEWORDS)
        hass.services.async_remove(DOMAIN, SERVICE_LIST_INSTALLED)
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH_REPOSITORIES)

    return unload_ok