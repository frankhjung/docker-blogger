#!/usr/bin/make

.PHONY: help install check coverage lock format lint test clean

.DEFAULT_GOAL := check

help: ## Show this help message
	@echo Available targets:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install dependencies
	@uv sync

lock: ## Regenerate uv.lock file for reproducible builds
	@uv lock
	@echo "Lock file updated. Commit with: git add uv.lock"

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
	@uv run pytest \
		--cov=blogspot_publishing \
		--cov-report=term-missing \
		--cov-report=html

check: format lint test coverage

clean: ## Clean build artifacts
	@$(RM) -rf .pytest_cache .ruff_cache .coverage htmlcov
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name '*.pyc' -delete

cleanall: clean ## Clean all generated files including venv
	@$(RM) -rf .venv

# Docker targets
build-image: ## Build the Docker image
	@docker build -t blogspot-publishing .

run-container: ## Run the Docker container (requires env vars or args)
	@docker run --rm blogspot-publishing \
		--source-file /data/public.index.html \
		--title "Post Title" \
		--labels "label1,label2" \
		--blog-id $(BLOG_ID) \
		--client-id $(CLIENT_ID) \
		--client-secret $(CLIENT_SECRET) \
		--refresh-token $(REFRESH_TOKEN)

test-container: build-image ## Test the Docker image (sanity check)
	@docker run --rm blogspot-publishing --help

version: build-image ## Show container version
	@docker run --rm blogspot-publishing --version
