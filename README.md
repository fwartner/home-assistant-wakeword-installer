# Wakeword Installer for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/fwartner/home-assistant-wakeword-installer.svg)](https://GitHub.com/fwartner/home-assistant-wakeword-installer/releases/)

A Home Assistant integration that allows you to manage and install wakeword files from GitHub repositories.

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

1. Copy the `wakeword_manager` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration > Integrations
4. Click "Add Integration" and search for "Wakeword Installer"

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

## Support

For issues and feature requests, please visit the [GitHub repository](https://github.com/fwartner/home-assistant-wakeword-installer).