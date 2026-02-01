#!/usr/bin/make

.PHONY: help install format lint test clean

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install dependencies
	@uv sync

format: ## Format code with ruff
	@uv run ruff format .

lint: ## Lint code with ruff
	@uv run ruff check .

lint-fix: ## Fix linting issues with ruff
	@uv run ruff check --fix .

test: ## Run tests with pytest
	@uv run pytest

test-verbose: ## Run tests with verbose output
	@uv run pytest -v

coverage: ## Run tests with coverage
	@uv run pytest --cov=blogspot_publishing --cov-report=term-missing --cov-report=html

check: format lint test ## Run all checks (format, lint, test)

clean: ## Clean build artifacts
	@$(RM) -rf .pytest_cache .ruff_cache .coverage htmlcov
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete

cleanall: clean ## Clean all generated files including venv
	@$(RM) -rf .venv
