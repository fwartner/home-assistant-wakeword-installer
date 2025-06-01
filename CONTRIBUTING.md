# Contributing to Wakeword Installer

Thank you for your interest in contributing to the Wakeword Installer for Home Assistant! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.11 or later
- Git
- Home Assistant development environment (optional but recommended)

### Setting up the Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/fwartner/home-assistant-wakeword-installer.git
   cd home-assistant-wakeword-installer
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Code Quality Tools

This project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security analysis
- **pytest**: Testing

### Running Code Quality Checks

```bash
# Format code
black custom_components/

# Sort imports
isort custom_components/

# Run linting
flake8 custom_components/

# Type checking
mypy custom_components/

# Security analysis
bandit -r custom_components/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=custom_components --cov-report=html

# Run specific test file
pytest tests/test_config_flow.py

# Run tests in verbose mode
pytest -v
```

### Testing Your Changes

1. **Unit Tests**: Ensure all existing tests pass and add tests for new functionality
2. **Integration Testing**: Test your changes in a real Home Assistant environment
3. **Manual Testing**: Verify the integration works as expected through the UI

## Code Style Guidelines

### Python Code

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Use descriptive variable and function names
- Keep functions small and focused on a single responsibility

### Example:

```python
async def get_available_languages(self, repo_url: str) -> list[str]:
    """Get available language folders from a GitHub repository.
    
    Args:
        repo_url: The GitHub repository URL.
        
    Returns:
        A list of available language folder names.
        
    Raises:
        HomeAssistantError: If the repository cannot be accessed.
    """
```

### Home Assistant Specifics

- Follow Home Assistant's [development guidelines](https://developers.home-assistant.io/)
- Use Home Assistant's logging system
- Handle exceptions appropriately with HomeAssistantError
- Use async/await for all I/O operations

## Submitting Changes

### Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, well-documented code
   - Add or update tests as needed
   - Update documentation if necessary

3. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request:**
   - Use a clear, descriptive title
   - Include a detailed description of your changes
   - Reference any related issues
   - Ensure all CI checks pass

### Commit Message Format

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding or updating tests
- `chore:` for maintenance tasks

## Reporting Issues

When reporting issues, please include:

- Home Assistant version
- Integration version
- Detailed description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Relevant log entries

## Development Tips

### Testing with Home Assistant

1. Create a `custom_components` directory in your HA config directory
2. Symlink or copy the `wakeword_installer` directory
3. Restart Home Assistant
4. Add the integration through the UI

### Debugging

- Enable debug logging in Home Assistant:
  ```yaml
  logger:
    default: info
    logs:
      custom_components.wakeword_installer: debug
  ```

- Use the Home Assistant developer tools for testing services

## Getting Help

- Check existing [issues](https://github.com/fwartner/home-assistant-wakeword-installer/issues)
- Review the [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
- Ask questions in the Home Assistant [Community Forum](https://community.home-assistant.io/)

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.