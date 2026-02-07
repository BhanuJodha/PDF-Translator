.PHONY: venv install install-dev test lint format typecheck clean build publish help

# Show help
help:
	@echo "PDF Translator - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make venv         Create virtual environment"
	@echo "  make install      Install package"
	@echo "  make install-dev  Install with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test         Run tests"
	@echo "  make test-cov     Run tests with coverage"
	@echo "  make lint         Check code style"
	@echo "  make lint-fix     Fix linting issues"
	@echo "  make format       Format code"
	@echo "  make typecheck    Run type checker"
	@echo "  make check        Run all checks"
	@echo ""
	@echo "Build:"
	@echo "  make build        Build package"
	@echo "  make publish-test Publish to Test PyPI"
	@echo "  make publish      Publish to PyPI"
	@echo "  make clean        Remove build artifacts"

# Create virtual environment
venv:
	python -m venv .venv
	@echo ""
	@echo "Virtual environment created! Activate it with:"
	@echo "  source .venv/bin/activate  (Linux/macOS)"
	@echo "  .venv\\Scripts\\activate     (Windows)"
	@echo ""
	@echo "Then run: make install-dev"

# Install package
install:
	pip install -e .

# Install with dev dependencies
install-dev:
	pip install -e ".[dev]"
	pre-commit install
	@echo ""
	@echo "Development environment ready!"

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ -v --cov=pdf_translator --cov-report=term-missing --cov-report=html

# Run linter
lint:
	ruff check pdf_translator tests

# Fix linting issues
lint-fix:
	ruff check pdf_translator tests --fix

# Format code
format:
	black pdf_translator tests

# Check formatting without changes
format-check:
	black pdf_translator tests --check

# Run type checker
typecheck:
	mypy pdf_translator --ignore-missing-imports

# Run all checks
check: format-check lint typecheck test

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build package
build: clean
	python -m build

# Publish to PyPI (use with caution)
publish: build
	python -m twine upload dist/*

# Publish to Test PyPI
publish-test: build
	python -m twine upload --repository testpypi dist/*
