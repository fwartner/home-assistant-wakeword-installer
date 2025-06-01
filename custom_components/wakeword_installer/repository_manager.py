"""Repository manager for handling GitHub repositories and wakeword files."""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import WAKEWORD_INSTALL_PATH

_LOGGER = logging.getLogger(__name__)


class RepositoryManager:
    """Manage GitHub repositories and wakeword installations."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the repository manager."""
        self.hass = hass
        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_available_languages(self, repo_url: str) -> list[str]:
        """Get available language folders from a GitHub repository."""
        try:
            # Convert GitHub URL to API URL
            api_url = self._convert_to_api_url(repo_url)
            
            async with self.session.get(api_url) as response:
                if response.status != 200:
                    raise HomeAssistantError(f"Failed to fetch repository contents: {response.status}")
                
                contents = await response.json()
                
                # Filter for directories (language folders)
                languages = []
                for item in contents:
                    if item["type"] == "dir":
                        languages.append(item["name"])
                
                return sorted(languages)
                
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Network error while fetching repository: {e}")
            raise HomeAssistantError(f"Cannot connect to repository: {e}")
        except Exception as e:
            _LOGGER.error(f"Error parsing repository contents: {e}")
            raise HomeAssistantError(f"Invalid repository structure: {e}")

    async def install_wakewords(self, repo_url: str, selected_languages: list[str]) -> None:
        """Install wakeword files from repository for selected languages."""
        try:
            # Create installation directory if it doesn't exist
            install_path = Path(WAKEWORD_INSTALL_PATH)
            install_path.mkdir(parents=True, exist_ok=True)
            
            # Download repository as zip
            download_url = self._get_download_url(repo_url)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "repo.zip"
                
                # Download the repository
                await self._download_file(download_url, zip_path)
                
                # Extract and install files
                await self._extract_and_install(zip_path, selected_languages, install_path)
                
            _LOGGER.info(f"Successfully installed wakewords for languages: {selected_languages}")
            
        except Exception as e:
            _LOGGER.error(f"Failed to install wakewords: {e}")
            raise HomeAssistantError(f"Installation failed: {e}")

    async def remove_wakewords(self, repo_name: str, languages: list[str]) -> None:
        """Remove installed wakeword files for specific languages."""
        try:
            install_path = Path(WAKEWORD_INSTALL_PATH)
            
            for language in languages:
                language_files = install_path.glob(f"*{repo_name}*{language}*.tflite")
                for file_path in language_files:
                    try:
                        file_path.unlink()
                        _LOGGER.info(f"Removed wakeword file: {file_path}")
                    except OSError as e:
                        _LOGGER.warning(f"Failed to remove file {file_path}: {e}")
                        
        except Exception as e:
            _LOGGER.error(f"Failed to remove wakewords: {e}")
            raise HomeAssistantError(f"Removal failed: {e}")

    def _convert_to_api_url(self, repo_url: str) -> str:
        """Convert GitHub repository URL to API URL."""
        # Handle different GitHub URL formats
        if repo_url.startswith("https://github.com/"):
            repo_path = repo_url.replace("https://github.com/", "")
        elif repo_url.startswith("github.com/"):
            repo_path = repo_url.replace("github.com/", "")
        else:
            raise HomeAssistantError("Invalid GitHub repository URL")
        
        # Remove .git suffix if present
        if repo_path.endswith(".git"):
            repo_path = repo_path[:-4]
        
        # Remove trailing slash
        repo_path = repo_path.rstrip("/")
        
        return f"https://api.github.com/repos/{repo_path}/contents"

    def _get_download_url(self, repo_url: str) -> str:
        """Get the download URL for the repository zip."""
        if repo_url.startswith("https://github.com/"):
            repo_path = repo_url.replace("https://github.com/", "")
        elif repo_url.startswith("github.com/"):
            repo_path = repo_url.replace("github.com/", "")
        else:
            raise HomeAssistantError("Invalid GitHub repository URL")
        
        if repo_path.endswith(".git"):
            repo_path = repo_path[:-4]
        
        repo_path = repo_path.rstrip("/")
        
        return f"https://github.com/{repo_path}/archive/refs/heads/main.zip"

    async def _download_file(self, url: str, file_path: Path) -> None:
        """Download a file from URL to local path."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise HomeAssistantError(f"Failed to download file: {response.status}")
                
                async with aiofiles.open(file_path, 'wb') as file:
                    async for chunk in response.content.iter_chunked(8192):
                        await file.write(chunk)
                        
        except aiohttp.ClientError as e:
            raise HomeAssistantError(f"Download failed: {e}")

    async def _extract_and_install(self, zip_path: Path, selected_languages: list[str], install_path: Path) -> None:
        """Extract zip file and install tflite files for selected languages."""
        def extract_sync():
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get all files in the zip
                all_files = zip_ref.namelist()
                
                # Filter for tflite files in selected language directories
                tflite_files = []
                for file_path in all_files:
                    if file_path.endswith('.tflite'):
                        # Check if file is in one of the selected language directories
                        path_parts = file_path.split('/')
                        if len(path_parts) >= 2:
                            # Check if any part of the path matches selected languages
                            for language in selected_languages:
                                if language in path_parts:
                                    tflite_files.append(file_path)
                                    break
                
                # Extract and install the tflite files
                for tflite_file in tflite_files:
                    try:
                        # Extract to temporary location
                        temp_file = zip_ref.extract(tflite_file)
                        
                        # Generate new filename with language prefix
                        original_name = Path(tflite_file).name
                        
                        # Try to determine language from path
                        language = "unknown"
                        path_parts = tflite_file.split('/')
                        for part in path_parts:
                            if part in selected_languages:
                                language = part
                                break
                        
                        new_name = f"{language}_{original_name}"
                        destination = install_path / new_name
                        
                        # Move file to installation directory
                        import shutil
                        shutil.move(temp_file, destination)
                        
                        _LOGGER.info(f"Installed wakeword: {new_name}")
                        
                    except Exception as e:
                        _LOGGER.warning(f"Failed to install {tflite_file}: {e}")
        
        # Run the synchronous extraction in a thread
        await asyncio.get_event_loop().run_in_executor(None, extract_sync)

    async def get_installed_wakewords(self) -> dict[str, list[str]]:
        """Get list of currently installed wakeword files organized by language."""
        try:
            install_path = Path(WAKEWORD_INSTALL_PATH)
            if not install_path.exists():
                return {}
            
            installed = {}
            for tflite_file in install_path.glob("*.tflite"):
                filename = tflite_file.name
                
                # Try to extract language from filename
                if "_" in filename:
                    language = filename.split("_")[0]
                else:
                    language = "unknown"
                
                if language not in installed:
                    installed[language] = []
                
                installed[language].append(filename)
            
            return installed
            
        except Exception as e:
            _LOGGER.error(f"Failed to get installed wakewords: {e}")
            return {}