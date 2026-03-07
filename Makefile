VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
HATCH := $(VENV_DIR)/bin/hatch

.PHONY: bootstrap
bootstrap:
	@if [ ! -d "$(VENV_DIR)" ]; then python3 -m venv $(VENV_DIR); fi
	@$(PIP) install --upgrade pip
	@$(PIP) install hatch

.PHONY: install
install: bootstrap
	@$(HATCH) env create

.PHONY: format
format: bootstrap
	@$(HATCH) run format

.PHONY: lint
lint: bootstrap
	@$(HATCH) run lint

.PHONY: test
test: bootstrap
	@$(HATCH) run test

.PHONY: coverage
coverage: bootstrap
	@$(HATCH) run test

.PHONY: check
check: lint test

.PHONY: check-all
check-all: format lint test build

.PHONY: build
build: bootstrap
	@$(HATCH) run build

.PHONY: clean
clean:
	@rm -rf .venv .pytest_cache .ruff_cache build dist *.egg-info
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

.PHONY: help
help:
	@echo "make install"
	@echo "make format"
	@echo "make lint"
	@echo "make test"
	@echo "make coverage"
	@echo "make check"
	@echo "make check-all"
	@echo "make build"
	@echo "make clean"
