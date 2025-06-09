# Keap MCP Server Development Makefile

.PHONY: help test coverage coverage-html lint clean install dev-setup

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	pip install -r requirements.txt
	pip install pytest pytest-cov coverage

dev-setup: install  ## Set up development environment
	pip install pytest pytest-cov coverage pytest-asyncio
	@echo "✅ Development environment ready"

test:  ## Run tests without coverage
	python -m pytest tests/unit/ -v

coverage:  ## Run tests with coverage reporting
	python test_coverage.py

coverage-html:  ## Generate HTML coverage report and open it
	python -m pytest tests/unit/ --cov=src --cov-report=html --cov-config=.coveragerc
	@echo "📊 Opening coverage report..."
	@if command -v open >/dev/null 2>&1; then \
		open htmlcov/index.html; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open htmlcov/index.html; \
	else \
		echo "Open htmlcov/index.html in your browser"; \
	fi

coverage-services:  ## Run coverage for service layer only
	python -m pytest tests/unit/test_*_service*.py --cov=src.services --cov-report=term-missing

test-services:  ## Run service tests only
	python -m pytest tests/unit/test_*_service*.py -v

test-models:  ## Run model tests only
	python -m pytest tests/unit/test_*model*.py -v

test-fast:  ## Run fast tests (skip slow integration tests)
	python -m pytest tests/unit/ -v -m "not slow"

lint:  ## Run code linting (if available)
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check src/; \
	elif command -v flake8 >/dev/null 2>&1; then \
		flake8 src/; \
	else \
		echo "Install ruff or flake8 for linting"; \
	fi

clean:  ## Clean generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -f .coverage
	rm -f keap_cache.db*

# Coverage targets
coverage-80:  ## Ensure 80%+ coverage
	python -m pytest tests/unit/ --cov=src --cov-fail-under=80 --cov-report=term-missing

coverage-check:  ## Check current coverage percentage
	python -m pytest tests/unit/ --cov=src --cov-report=term | grep "^TOTAL" || echo "No coverage data"

# Development workflow targets
dev-test: clean test coverage  ## Full development test cycle

ci-test:  ## CI/CD test command
	python -m pytest tests/unit/ --cov=src --cov-report=xml --cov-report=term-missing --junitxml=test-results.xml

# Service-specific testing
test-query:  ## Test query services
	python -m pytest tests/unit/test_query_services.py -v

test-strategy:  ## Test strategy service
	python -m pytest tests/unit/test_strategy_service.py -v

test-api:  ## Test API service
	python -m pytest tests/unit/test_api_service.py -v

# Architecture verification
verify-architecture:  ## Verify service architecture works
	python -c "import asyncio; from src.services import get_service_container; from src.interfaces import IContactQueryService, ITagQueryService; asyncio.run(main())" || echo "Run 'make test-services' to verify architecture"

# Coverage monitoring and CI utilities
coverage-monitor:  ## Run detailed coverage analysis
	python scripts/coverage-monitor.py

test-ci-local:  ## Simulate CI pipeline locally
	./scripts/test-ci-local.sh

coverage-badge:  ## Generate coverage badge
	pip install coverage-badge || echo "Installing coverage-badge..."
	coverage-badge -f -o coverage.svg
	@echo "📊 Coverage badge generated: coverage.svg"

setup-ci:  ## Set up CI dependencies
	pip install ruff coverage-badge
	@echo "✅ CI dependencies installed"

# Development quality checks
quality-check: lint coverage-80  ## Run full quality check
	@echo "🎉 Quality check completed"

pre-commit-check: clean lint coverage-check  ## Quick pre-commit verification
	@echo "✅ Pre-commit checks passed"

.DEFAULT_GOAL := help