.PHONY: help install install-dev lint format type-check security clean pre-commit setup-dev

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  setup-dev    - Complete development setup"
	@echo "  lint         - Run all linting checks"
	@echo "  format       - Format code with black and isort"
	@echo "  type-check   - Run mypy type checking"
	@echo "  security     - Run security checks"
	@echo "  pre-commit   - Run pre-commit hooks"
	@echo "  clean        - Clean up temporary files"

# Install production dependencies
install:
	pip install -e .

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

# Complete development setup
setup-dev: install-dev
	pre-commit install
	@echo "Development environment is ready!"

# Run all linting checks
lint: format type-check security
	flake8 custom_components/
	yamllint .github/workflows/
	codespell

# Format code
format:
	black custom_components/
	isort custom_components/

# Type checking
type-check:
	mypy custom_components/

# Security checks
security:
	bandit -r custom_components/
	safety check

# Run pre-commit hooks on all files
pre-commit:
	pre-commit run --all-files

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -f bandit-report.json safety-report.json

# CI commands
ci-lint: lint

ci-security: security