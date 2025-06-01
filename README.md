# Wakeword Installer for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/fwartner/home-assistant-wakeword-installer.svg)](https://GitHub.com/fwartner/home-assistant-wakeword-installer/releases/)
[![CI](https://github.com/fwartner/home-assistant-wakeword-installer/workflows/CI/badge.svg)](https://github.com/fwartner/home-assistant-wakeword-installer/actions/workflows/ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

A powerful Home Assistant integration that simplifies the management and installation of wakeword files from GitHub repositories. Designed for seamless integration with voice assistants like Wyoming, openWakeWord, and other wake word detection systems.

> **Compatible with**: Home Assistant 2024.1.0+ | **HACS Ready** | **Multi-Language Support**

## Features

- **Multi-Repository Support**: Add multiple GitHub repositories containing wakeword files
- **Language Selection**: Choose specific languages from each repository
- **Automatic Installation**: Downloads and installs .tflite files to the correct Home Assistant directory
- **Repository Management**: Add, remove, and manage repositories through the UI
- **Service Calls**: Programmatically install/remove wakewords via services
- **HACS Compatible**: Easy installation and updates through HACS

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations" 
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/fwartner/home-assistant-wakeword-installer` as repository
6. Select "Integration" as category
7. Click "Add"
8. Find "Wakeword Installer" in HACS and install it
9. Restart Home Assistant
10. Go to Configuration > Integrations > Add Integration > "Wakeword Installer"

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/fwartner/home-assistant-wakeword-installer/releases)
2. Extract the contents and copy the `wakeword_installer` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Go to Configuration > Integrations
5. Click "Add Integration" and search for "Wakeword Installer"

### Requirements

- Home Assistant 2024.1.0 or later
- Internet connection for downloading repositories
- Write access to `/share/openwakeword/` directory

## Configuration

### Adding Repositories

1. When setting up the integration, enter:
   - **Repository Name**: A friendly name for the repository
   - **Repository URL**: The GitHub repository URL (e.g., `https://github.com/username/wakewords-repo`)

2. Select the languages you want to install from the repository

3. Optionally add more repositories

### Repository Structure

Your GitHub repository should be organized with language subfolders containing .tflite files:

```
repository/
├── english/
│   ├── hey_assistant.tflite
│   └── wake_up.tflite
├── german/
│   ├── hallo_assistent.tflite
│   └── aufwachen.tflite
└── spanish/
    ├── hola_asistente.tflite
    └── despertar.tflite
```

## Management

### Through the UI

1. Go to Configuration > Integrations
2. Find "Wakeword Manager" and click "Configure"
3. Use the options to:
   - Add new repositories
   - Remove existing repositories
   - Install wakewords from all configured repositories

### Through Services

The integration provides several services:

#### `wakeword_installer.install_wakewords`
Install wakewords from configured repositories.

```yaml
service: wakeword_installer.install_wakewords
data:
  repository: "my-wakewords"  # Optional: specific repository
  languages: ["english", "german"]  # Optional: specific languages
```

#### `wakeword_installer.remove_wakewords`
Remove installed wakeword files.

```yaml
service: wakeword_installer.remove_wakewords
data:
  repository: "my-wakewords"
  languages: ["english"]
```

#### `wakeword_installer.list_installed`
Get a list of currently installed wakeword files.

```yaml
service: wakeword_installer.list_installed
```

#### `wakeword_installer.refresh_repositories`
Refresh available languages from all configured repositories.

```yaml
service: wakeword_installer.refresh_repositories
```

## File Installation

Wakeword files are installed to `/share/openwakeword/` with the naming convention:
`{language}_{original_filename}.tflite`

For example: `english_hey_assistant.tflite`

## Supported Repository Formats

- Public GitHub repositories
- Repositories with language-based folder structure
- .tflite wakeword files

## Troubleshooting

### Repository Not Found
- Ensure the GitHub repository URL is correct and publicly accessible
- Check that the repository contains .tflite files in language subdirectories

### Installation Fails
- Verify Home Assistant has write permissions to `/share/openwakeword/`
- Check the Home Assistant logs for detailed error messages

### No Languages Found
- Ensure your repository has subdirectories containing .tflite files
- The integration looks for directories in the repository root

## Example Repository

Check out the example repository structure at: https://github.com/fwartner/home-assistant-wakewords-collection

## Supported Wakeword Systems

This integration is compatible with:

- **openWakeWord**: Open-source wake word detection
- **Wyoming Protocol**: Home Assistant's voice assistant ecosystem
- **Piper**: Neural text-to-speech system
- **Whisper**: Automatic speech recognition
- **Any system that uses .tflite files**: Custom implementations

## Community Examples

### Popular Wakeword Repositories

- [Home Assistant Wakewords Collection](https://github.com/fwartner/home-assistant-wakewords-collection) - Curated collection of community wakewords
- Create your own repository following the [structure guidelines](#repository-structure)

### Creating Your Own Wakeword Repository

1. Create a public GitHub repository
2. Organize .tflite files in language subdirectories:
   ```
   your-repo/
   ├── english/
   │   ├── hey_assistant.tflite
   │   └── wake_up.tflite
   ├── german/
   │   ├── hallo_assistent.tflite
   │   └── aufwachen.tflite
   └── README.md
   ```
3. Share your repository URL with the community

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/fwartner/home-assistant-wakeword-installer.git
cd home-assistant-wakeword-installer

# Install development dependencies
make setup-dev

# Run linting and type checking
make lint
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and releases.

## Support

### Getting Help

- 📚 [Documentation](https://github.com/fwartner/home-assistant-wakeword-installer/blob/main/README.md)
- 🐛 [Issue Tracker](https://github.com/fwartner/home-assistant-wakeword-installer/issues)
- 💬 [Home Assistant Community](https://community.home-assistant.io/)
- 📧 [Contact](mailto:hi@fwartner.com)

### Reporting Issues

When reporting issues, please include:

- Home Assistant version
- Integration version
- Error messages from logs
- Steps to reproduce
- Repository URL (if applicable)

---

**Star ⭐ this repository if you find it useful!**