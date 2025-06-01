# Wakeword Installer

A powerful Home Assistant integration that simplifies the management and installation of wakeword files from GitHub repositories.

## 🚀 Quick Start

1. **Add Repository**: Enter your GitHub repository URL containing wakeword files
2. **Select Languages**: Choose which languages to install from the repository
3. **Install**: Files are automatically downloaded and installed to the correct directory
4. **Manage**: Add multiple repositories and manage them through the UI

## ✨ Key Features

- **🔄 Multi-Repository Support**: Manage multiple GitHub repositories
- **🌍 Language Selection**: Choose specific languages from each repository
- **⚡ Automatic Installation**: Downloads and installs .tflite files automatically
- **🧹 Smart Cleanup**: Removing repositories automatically cleans up files
- **🔧 Service Integration**: Full service support for automation
- **🌐 Multi-Language**: English and German translations included

## 📁 Repository Structure

Your GitHub repository should be organized like this:

```
your-wakewords-repo/
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

## 🎯 Perfect For

- **openWakeWord**: Open-source wake word detection
- **Wyoming Protocol**: Home Assistant's voice ecosystem
- **Custom Voice Assistants**: Any system using .tflite files
- **Multi-Language Setups**: Support for multiple languages

## 🛠️ Services Available

- `install_wakewords`: Install from repositories
- `remove_wakewords`: Remove specific language files
- `remove_repository_wakewords`: Remove all files from a repository
- `list_installed`: See what's currently installed
- `refresh_repositories`: Update available languages

## 📍 Installation Path

Files are installed to: `/share/openwakeword/`

Naming format: `{repository}_{language}_{filename}.tflite`

## 🔧 Automation Example

```yaml
automation:
  - alias: "Install German Wakewords"
    trigger:
      platform: state
      entity_id: input_boolean.install_german_voice
      to: 'on'
    action:
      service: wakeword_installer.install_wakewords
      data:
        repository: "my-wakewords"
        languages: ["german"]
```

## 🌟 Get Started

Ready to enhance your Home Assistant voice experience? Install the Wakeword Installer and start managing your wake words effortlessly!
