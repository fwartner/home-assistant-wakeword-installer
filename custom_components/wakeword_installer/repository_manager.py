"""Repository manager for handling GitHub repositories and wakeword files."""
from __future__ import annotations

import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import aiofiles
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import WAKEWORD_INSTALL_PATH

_LOGGER = logging.getLogger(__name__)

# Safety limits
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=120, connect=30)
MAX_DOWNLOAD_SIZE = 500 * 1024 * 1024  # 500 MB
GITHUB_HOST = "github.com"
REQUEST_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "home-assistant-wakeword-installer",
}


class RepositoryManager:
    """Manage GitHub repositories and wakeword installations."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the repository manager."""
        self.hass = hass
        self.session = aiohttp.ClientSession(timeout=HTTP_TIMEOUT)

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_available_languages(self, repo_url: str) -> list[str]:
        """Get available language folders from a GitHub repository."""
        try:
            api_url = self._convert_to_api_url(repo_url)

            async with self.session.get(api_url, headers=REQUEST_HEADERS) as response:
                if response.status != 200:
                    raise HomeAssistantError(
                        f"Failed to fetch repository contents: {response.status}"
                    )

                contents = await response.json()

                languages = [
                    item["name"]
                    for item in contents
                    if item["type"] == "dir" and not item["name"].startswith(".")
                ]
                return sorted(languages)

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error while fetching repository: %s", err)
            raise HomeAssistantError(f"Cannot connect to repository: {err}")
        except HomeAssistantError:
            raise
        except Exception as err:
            _LOGGER.error("Error parsing repository contents: %s", err)
            raise HomeAssistantError(f"Invalid repository structure: {err}")

    async def install_wakewords(
        self,
        repo_url: str,
        selected_languages: list[str],
        repo_name: str | None = None,
    ) -> None:
        """Install wakeword files from repository for selected languages."""
        try:
            install_path = Path(WAKEWORD_INSTALL_PATH)
            await self.hass.async_add_executor_job(
                install_path.mkdir, 0o777, True, True
            )

            if repo_name is None:
                repo_name = self._extract_repo_name(repo_url)
            # Safety: if repo_name looks like a URL, extract just the name
            if "/" in repo_name:
                repo_name = self._extract_repo_name(repo_name)

            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "repo.zip"
                download_errors: list[str] = []
                downloaded = False

                for download_url in await self._get_download_urls(repo_url):
                    try:
                        await self._download_file(download_url, zip_path)
                        downloaded = True
                        break
                    except HomeAssistantError as err:
                        download_errors.append(str(err))
                        _LOGGER.debug(
                            "Archive download failed for %s: %s",
                            download_url,
                            err,
                        )

                if not downloaded:
                    joined_errors = "; ".join(download_errors) or "unknown error"
                    raise HomeAssistantError(
                        f"Failed to download repository archive: {joined_errors}"
                    )

                await self._extract_and_install(
                    zip_path, selected_languages, install_path, repo_name, temp_dir
                )

            _LOGGER.info(
                "Successfully installed wakewords for languages: %s",
                selected_languages,
            )

        except HomeAssistantError:
            raise
        except Exception as err:
            _LOGGER.error("Failed to install wakewords: %s", err)
            raise HomeAssistantError(f"Installation failed: {err}")

    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        try:
            repo_path = self._normalize_repo_path(repo_url)
        except HomeAssistantError:
            return "unknown-repo"

        return repo_path.split("/")[-1]

    async def remove_wakewords(
        self, repo_name: str, languages: list[str] | None = None
    ) -> None:
        """Remove installed wakeword files.

        Args:
            repo_name: Name of the repository.
            languages: Languages to remove. If None, removes all from this repo.
        """

        def _remove_sync() -> None:
            install_path = Path(WAKEWORD_INSTALL_PATH)
            if not install_path.exists():
                return

            if languages is None:
                # Format: {repo_name}_{language}_{original_name}.tflite
                for file_path in install_path.glob("%s_*.tflite" % repo_name):
                    try:
                        file_path.unlink()
                        _LOGGER.info("Removed wakeword file: %s", file_path.name)
                    except OSError as err:
                        _LOGGER.warning(
                            "Failed to remove file %s: %s", file_path, err
                        )
            else:
                for language in languages:
                    pattern = "%s_%s_*.tflite" % (repo_name, language)
                    for file_path in install_path.glob(pattern):
                        try:
                            file_path.unlink()
                            _LOGGER.info(
                                "Removed wakeword file: %s", file_path.name
                            )
                        except OSError as err:
                            _LOGGER.warning(
                                "Failed to remove file %s: %s", file_path, err
                            )

        try:
            await self.hass.async_add_executor_job(_remove_sync)
        except Exception as err:
            _LOGGER.error("Failed to remove wakewords: %s", err)
            raise HomeAssistantError(f"Removal failed: {err}")

    async def remove_repository_wakewords(self, repo_name: str) -> None:
        """Remove all wakeword files associated with a repository."""
        await self.remove_wakewords(repo_name, languages=None)

    def _convert_to_api_url(self, repo_url: str) -> str:
        """Convert GitHub repository URL to API URL."""
        repo_path = self._normalize_repo_path(repo_url)
        return f"https://api.github.com/repos/{repo_path}/contents"

    def _normalize_repo_path(self, repo_url: str) -> str:
        """Normalize a GitHub repository URL to owner/repo."""
        normalized_url = repo_url.strip()
        if normalized_url.startswith(f"{GITHUB_HOST}/"):
            normalized_url = f"https://{normalized_url}"

        parsed = urlparse(normalized_url)
        if (
            parsed.scheme not in {"http", "https"}
            or parsed.netloc.lower() not in {GITHUB_HOST, f"www.{GITHUB_HOST}"}
        ):
            raise HomeAssistantError("Invalid GitHub repository URL")

        repo_path = parsed.path.strip("/")
        if repo_path.endswith(".git"):
            repo_path = repo_path[:-4]

        parts = [part for part in repo_path.split("/") if part]
        if len(parts) < 2:
            raise HomeAssistantError("Invalid GitHub repository URL")

        return f"{parts[0]}/{parts[1]}"

    async def _get_default_branch(self, repo_url: str) -> str:
        """Return the repository default branch, falling back to main."""
        repo_path = self._normalize_repo_path(repo_url)
        repo_api_url = f"https://api.github.com/repos/{repo_path}"
        try:
            async with self.session.get(
                repo_api_url, headers=REQUEST_HEADERS
            ) as response:
                if response.status != 200:
                    return "main"

                repo_info = await response.json()
                default_branch = repo_info.get("default_branch")
                if isinstance(default_branch, str) and default_branch:
                    return default_branch
        except (aiohttp.ClientError, ValueError):
            _LOGGER.debug(
                "Unable to resolve default branch for %s; falling back to main",
                repo_url,
            )

        return "main"

    async def _get_download_urls(self, repo_url: str) -> list[str]:
        """Build download URL candidates for repository archive retrieval."""
        repo_path = self._normalize_repo_path(repo_url)
        default_branch = await self._get_default_branch(repo_url)
        branch_candidates = [default_branch, "main", "master"]
        seen_branches: set[str] = set()
        urls: list[str] = []
        for branch in branch_candidates:
            if branch in seen_branches:
                continue
            seen_branches.add(branch)
            urls.append(
                f"https://github.com/{repo_path}/archive/refs/heads/{branch}.zip"
            )

        return urls

    async def _download_file(self, url: str, file_path: Path) -> None:
        """Download a file from URL to local path with size limit."""
        try:
            async with self.session.get(url, headers=REQUEST_HEADERS) as response:
                if response.status != 200:
                    raise HomeAssistantError(
                        f"Failed to download file ({response.status}) from {url}"
                    )

                # Check content-length if available
                content_length = response.content_length
                if content_length and content_length > MAX_DOWNLOAD_SIZE:
                    raise HomeAssistantError(
                        f"Download too large: {content_length} bytes "
                        f"(max {MAX_DOWNLOAD_SIZE})"
                    )

                total_size = 0
                async with aiofiles.open(file_path, "wb") as file:
                    async for chunk in response.content.iter_chunked(8192):
                        total_size += len(chunk)
                        if total_size > MAX_DOWNLOAD_SIZE:
                            raise HomeAssistantError(
                                f"Download exceeded size limit of {MAX_DOWNLOAD_SIZE} bytes"
                            )
                        await file.write(chunk)

        except aiohttp.ClientError as err:
            raise HomeAssistantError(f"Download failed: {err}")

    async def _extract_and_install(
        self,
        zip_path: Path,
        selected_languages: list[str],
        install_path: Path,
        repo_name: str,
        temp_dir: str,
    ) -> None:
        """Extract zip file and install tflite files for selected languages."""

        def extract_sync() -> None:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                all_files = zip_ref.namelist()

                tflite_files = []
                for entry in all_files:
                    if entry.endswith(".tflite"):
                        path_parts = entry.split("/")
                        if len(path_parts) >= 2:
                            for language in selected_languages:
                                if language in path_parts:
                                    tflite_files.append(entry)
                                    break

                for tflite_file in tflite_files:
                    try:
                        # Zip-slip protection: extract to temp_dir and validate
                        member_info = zip_ref.getinfo(tflite_file)
                        extracted = zip_ref.extract(member_info, path=temp_dir)
                        real_extracted = os.path.realpath(extracted)
                        real_temp = os.path.realpath(temp_dir)
                        if not real_extracted.startswith(real_temp + os.sep):
                            _LOGGER.warning(
                                "Skipping suspicious zip entry: %s", tflite_file
                            )
                            continue

                        original_name = Path(tflite_file).name

                        language = "unknown"
                        path_parts = tflite_file.split("/")
                        for part in path_parts:
                            if part in selected_languages:
                                language = part
                                break

                        # Format: {repo_name}_{language}_{original_name}
                        new_name = "%s_%s_%s" % (repo_name, language, original_name)
                        destination = install_path / new_name

                        shutil.move(extracted, destination)

                        _LOGGER.info("Installed wakeword: %s", new_name)

                    except Exception as err:
                        _LOGGER.warning(
                            "Failed to install %s: %s", tflite_file, err
                        )

        await self.hass.async_add_executor_job(extract_sync)

    async def get_installed_wakewords(self) -> dict[str, list[str]]:
        """Get list of currently installed wakeword files organized by language."""

        def _list_sync() -> dict[str, list[str]]:
            install_path = Path(WAKEWORD_INSTALL_PATH)
            if not install_path.exists():
                return {}

            installed: dict[str, list[str]] = {}
            for tflite_file in install_path.glob("*.tflite"):
                filename = tflite_file.name

                # Format: {repo_name}_{language}_{original_name}
                parts = filename.split("_")
                if len(parts) >= 3:
                    language = parts[1]
                else:
                    language = "unknown"

                if language not in installed:
                    installed[language] = []

                installed[language].append(filename)

            return installed

        try:
            return await self.hass.async_add_executor_job(_list_sync)
        except Exception as err:
            _LOGGER.error("Failed to get installed wakewords: %s", err)
            return {}
