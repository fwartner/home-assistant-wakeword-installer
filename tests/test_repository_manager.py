"""Tests for the RepositoryManager."""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.exceptions import HomeAssistantError

from custom_components.wakeword_installer.repository_manager import RepositoryManager


@pytest.fixture
def repo_manager(mock_hass: MagicMock) -> RepositoryManager:
    """Create a RepositoryManager with mocked session."""
    with patch("custom_components.wakeword_installer.repository_manager.aiohttp.ClientSession") as mock_cs:
        manager = RepositoryManager(mock_hass)
        # Replace with a controllable mock
        manager.session = AsyncMock()
        manager.session.closed = False
        return manager


# --- URL conversion tests ---


class TestConvertToApiUrl:
    """Test _convert_to_api_url."""

    def test_standard_github_url(self, repo_manager: RepositoryManager) -> None:
        result = repo_manager._convert_to_api_url("https://github.com/user/repo")
        assert result == "https://api.github.com/repos/user/repo/contents"

    def test_github_url_with_trailing_slash(self, repo_manager: RepositoryManager) -> None:
        result = repo_manager._convert_to_api_url("https://github.com/user/repo/")
        assert result == "https://api.github.com/repos/user/repo/contents"

    def test_github_url_with_git_suffix(self, repo_manager: RepositoryManager) -> None:
        result = repo_manager._convert_to_api_url("https://github.com/user/repo.git")
        assert result == "https://api.github.com/repos/user/repo/contents"

    def test_github_url_without_https(self, repo_manager: RepositoryManager) -> None:
        result = repo_manager._convert_to_api_url("github.com/user/repo")
        assert result == "https://api.github.com/repos/user/repo/contents"

    def test_invalid_url_raises(self, repo_manager: RepositoryManager) -> None:
        with pytest.raises(HomeAssistantError, match="Invalid GitHub repository URL"):
            repo_manager._convert_to_api_url("https://gitlab.com/user/repo")


class TestGetDownloadUrl:
    """Test _get_download_url."""

    def test_standard_url(self, repo_manager: RepositoryManager) -> None:
        result = repo_manager._get_download_url("https://github.com/user/repo")
        assert result == "https://github.com/user/repo/archive/refs/heads/main.zip"

    def test_url_with_git_suffix(self, repo_manager: RepositoryManager) -> None:
        result = repo_manager._get_download_url("https://github.com/user/repo.git")
        assert result == "https://github.com/user/repo/archive/refs/heads/main.zip"

    def test_invalid_url_raises(self, repo_manager: RepositoryManager) -> None:
        with pytest.raises(HomeAssistantError):
            repo_manager._get_download_url("https://gitlab.com/user/repo")


class TestExtractRepoName:
    """Test _extract_repo_name."""

    def test_standard_url(self, repo_manager: RepositoryManager) -> None:
        assert repo_manager._extract_repo_name("https://github.com/user/my-repo") == "my-repo"

    def test_url_with_git_suffix(self, repo_manager: RepositoryManager) -> None:
        assert repo_manager._extract_repo_name("https://github.com/user/my-repo.git") == "my-repo"

    def test_url_without_https(self, repo_manager: RepositoryManager) -> None:
        assert repo_manager._extract_repo_name("github.com/user/my-repo") == "my-repo"

    def test_unknown_url(self, repo_manager: RepositoryManager) -> None:
        assert repo_manager._extract_repo_name("https://gitlab.com/user/repo") == "unknown-repo"


# --- Async operation tests ---


@pytest.mark.asyncio
class TestGetAvailableLanguages:
    """Test get_available_languages."""

    @staticmethod
    def _mock_context_manager(response):
        """Create a mock async context manager that returns the given response."""
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=response)
        ctx.__aexit__ = AsyncMock(return_value=False)
        return ctx

    async def test_returns_sorted_language_dirs(
        self, repo_manager: RepositoryManager, github_api_response: list[dict]
    ) -> None:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=github_api_response)
        repo_manager.session.get = MagicMock(return_value=self._mock_context_manager(mock_response))

        result = await repo_manager.get_available_languages("https://github.com/test/wakewords")
        assert result == ["de", "en", "fr"]

    async def test_non_200_raises(self, repo_manager: RepositoryManager) -> None:
        mock_response = AsyncMock()
        mock_response.status = 404
        repo_manager.session.get = MagicMock(return_value=self._mock_context_manager(mock_response))

        with pytest.raises(HomeAssistantError, match="Invalid repository structure"):
            await repo_manager.get_available_languages("https://github.com/test/wakewords")

    async def test_empty_repo_returns_empty(self, repo_manager: RepositoryManager) -> None:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=[{"name": "README.md", "type": "file"}])
        repo_manager.session.get = MagicMock(return_value=self._mock_context_manager(mock_response))

        result = await repo_manager.get_available_languages("https://github.com/test/wakewords")
        assert result == []


@pytest.mark.asyncio
class TestClose:
    """Test session closing."""

    async def test_close_open_session(self, repo_manager: RepositoryManager) -> None:
        repo_manager.session.closed = False
        await repo_manager.close()
        repo_manager.session.close.assert_called_once()

    async def test_close_already_closed(self, repo_manager: RepositoryManager) -> None:
        repo_manager.session.closed = True
        await repo_manager.close()
        repo_manager.session.close.assert_not_called()


@pytest.mark.asyncio
class TestInstallWakewords:
    """Test install_wakewords with a real zip file."""

    async def test_install_creates_files(self, repo_manager: RepositoryManager) -> None:
        """Test the full install flow with a real temp zip containing tflite files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            install_path = Path(tmpdir) / "openwakeword"

            # Build a real zip that mimics a GitHub archive
            zip_path = Path(tmpdir) / "repo.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("repo-main/en/hey_jarvis.tflite", b"fake-model-en")
                zf.writestr("repo-main/de/hallo_jarvis.tflite", b"fake-model-de")
                zf.writestr("repo-main/fr/bonjour.tflite", b"fake-model-fr")

            # Patch constants and download to use our temp zip
            with (
                patch("custom_components.wakeword_installer.repository_manager.WAKEWORD_INSTALL_PATH", str(install_path)),
                patch.object(repo_manager, "_download_file", new_callable=AsyncMock) as mock_dl,
            ):
                # Make _download_file copy our pre-built zip to the expected path
                async def fake_download(url, dest):
                    import shutil
                    shutil.copy2(zip_path, dest)

                mock_dl.side_effect = fake_download

                await repo_manager.install_wakewords(
                    "https://github.com/test/wakewords",
                    ["en", "de"],
                    "test-repo",
                )

            # Verify tflite files were installed (en and de, not fr)
            installed = list(install_path.glob("*.tflite"))
            names = sorted(f.name for f in installed)
            assert len(names) == 2
            assert any("en" in n for n in names)
            assert any("de" in n for n in names)
            assert not any("fr" in n for n in names)


@pytest.mark.asyncio
class TestRemoveWakewords:
    """Test wakeword removal."""

    async def test_remove_specific_languages(self, repo_manager: RepositoryManager) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            install_path = Path(tmpdir)
            # Create fake installed files
            (install_path / "en_test-repo_hey.tflite").write_bytes(b"x")
            (install_path / "de_test-repo_hallo.tflite").write_bytes(b"x")

            with patch("custom_components.wakeword_installer.repository_manager.WAKEWORD_INSTALL_PATH", str(install_path)):
                await repo_manager.remove_wakewords("test-repo", ["en"])

            remaining = list(install_path.glob("*.tflite"))
            assert len(remaining) == 1
            assert "de" in remaining[0].name

    async def test_remove_all_for_repo(self, repo_manager: RepositoryManager) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            install_path = Path(tmpdir)
            (install_path / "en_test-repo_hey.tflite").write_bytes(b"x")
            (install_path / "de_test-repo_hallo.tflite").write_bytes(b"x")
            (install_path / "en_other-repo_hi.tflite").write_bytes(b"x")

            with patch("custom_components.wakeword_installer.repository_manager.WAKEWORD_INSTALL_PATH", str(install_path)):
                await repo_manager.remove_wakewords("test-repo", languages=None)

            remaining = list(install_path.glob("*.tflite"))
            assert len(remaining) == 1
            assert "other-repo" in remaining[0].name


@pytest.mark.asyncio
class TestGetInstalledWakewords:
    """Test listing installed wakewords."""

    async def test_returns_grouped_by_language(self, repo_manager: RepositoryManager) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            install_path = Path(tmpdir)
            (install_path / "en_repo_hey.tflite").write_bytes(b"x")
            (install_path / "en_repo_hi.tflite").write_bytes(b"x")
            (install_path / "de_repo_hallo.tflite").write_bytes(b"x")

            with patch("custom_components.wakeword_installer.repository_manager.WAKEWORD_INSTALL_PATH", str(install_path)):
                result = await repo_manager.get_installed_wakewords()

            assert "en" in result
            assert "de" in result
            assert len(result["en"]) == 2
            assert len(result["de"]) == 1

    async def test_empty_dir_returns_empty(self, repo_manager: RepositoryManager) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("custom_components.wakeword_installer.repository_manager.WAKEWORD_INSTALL_PATH", str(tmpdir)):
                result = await repo_manager.get_installed_wakewords()
            assert result == {}

    async def test_nonexistent_dir_returns_empty(self, repo_manager: RepositoryManager) -> None:
        with patch("custom_components.wakeword_installer.repository_manager.WAKEWORD_INSTALL_PATH", "/nonexistent/path"):
            result = await repo_manager.get_installed_wakewords()
        assert result == {}
