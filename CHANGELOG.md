# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Wakeword Installer integration
- Multi-repository support for GitHub wakeword repositories
- Language selection and filtering
- Automatic file installation to `/share/openwakeword/`
- Repository management through Home Assistant UI
- Service calls for programmatic control
- English and German translations
- HACS compatibility
- Comprehensive CI/CD pipeline
- Security scanning and code quality checks

### Features
- **Multi-Repository Management**: Add, remove, and manage multiple GitHub repositories
- **Language Support**: Select specific languages from each repository
- **Automatic Cleanup**: Repository deletion automatically removes associated files
- **Service Integration**: Full service support for automation
- **Translation Ready**: English and German language support
- **HACS Ready**: Full compatibility with Home Assistant Community Store

### Services
- `install_wakewords`: Install wakewords from configured repositories
- `remove_wakewords`: Remove wakewords for specific languages
- `remove_repository_wakewords`: Remove all wakewords from a repository
- `list_installed`: List currently installed wakeword files
- `refresh_repositories`: Refresh available languages from repositories

## [1.0.0] - 2025-01-06

### Added
- Initial release

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A