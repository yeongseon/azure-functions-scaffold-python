VENV_DIR := .venv
# The interpreter you select: it builds the virtual environment.
PYTHON ?= python3
PIP := $(VENV_DIR)/bin/pip
HATCH := $(VENV_DIR)/bin/hatch

# Idempotent: installs Hatch only while it is missing and never upgrades pip.
.PHONY: bootstrap
bootstrap:
	@if [ ! -x "$(HATCH)" ]; then \
		{ [ -d "$(VENV_DIR)" ] || $(PYTHON) -m venv $(VENV_DIR); } && \
		echo "Installing Hatch into $(VENV_DIR)..." && \
		$(PIP) install --disable-pip-version-check --quiet hatch; \
	fi

.PHONY: ensure-hatch
ensure-hatch: bootstrap

.PHONY: install
install: ensure-hatch
	@$(HATCH) env create
	@if [ -n "$$CI" ]; then \
		echo "CI detected: skipping pre-commit hook installation"; \
	else \
		$(MAKE) precommit-install; \
	fi

.PHONY: shell
shell: ensure-hatch
	@$(HATCH) shell

.PHONY: reset
reset: clean-all install
	@echo "Project reset complete."

.PHONY: hatch-clean
hatch-clean: ensure-hatch
	@$(HATCH) env remove || echo "No hatch environment to remove"

.PHONY: format
format: ensure-hatch
	@$(HATCH) run format

.PHONY: format-check
format-check: ensure-hatch
	@$(HATCH) run format-check

.PHONY: style
style: ensure-hatch
	@$(HATCH) run style

.PHONY: typecheck
typecheck: ensure-hatch
	@$(HATCH) run typecheck

.PHONY: lint
lint: ensure-hatch
	@$(HATCH) run lint

.PHONY: security
security: ensure-hatch
	@$(HATCH) run security
	@$(MAKE) security-bandit security-rendered

# Security entry points are separate to minimize verification-branch conflicts.
SECURITY_RUN ?= $(HATCH) run python
SECURITY_OUTPUT ?= security-results
AUDIT_SITE_PACKAGES ?=
CANDIDATE_NAME ?= azure-functions-scaffold
CANDIDATE_VERSION ?=
AUDIT_FLAGS ?=
SEMGREP_OUTCOME ?=

.PHONY: security-rendered security-bandit security-semgrep security-audit security-audit-report security-host security-contracts
security-rendered:
	@$(SECURITY_RUN) -m tools.rendered_security --output $(SECURITY_OUTPUT)/rendered
security-bandit:
	@$(SECURITY_RUN) -m tools.security_evidence bandit --output $(SECURITY_OUTPUT)/bandit
security-semgrep:
	@status=0; $(SECURITY_RUN) -m tools.security_evidence semgrep --outcome "$(SEMGREP_OUTCOME)" --output $(SECURITY_OUTPUT)/semgrep || status=$$?; test $$status -eq 0 -o $$status -eq 3
security-audit:
	@$(SECURITY_RUN) -m tools.dependency_audit_policy --site-packages "$(AUDIT_SITE_PACKAGES)" --candidate-name "$(CANDIDATE_NAME)" --candidate-version "$(CANDIDATE_VERSION)" $(AUDIT_FLAGS) --output $(SECURITY_OUTPUT)
security-audit-report:
	@status=0; $(MAKE) security-audit || status=$$?; echo "Reporting-only dependency audit exit code: $$status"
security-host:
	@RUN_LOCAL_HOST_SECURITY=true $(HATCH) run pytest -o addopts= tests/test_generated_langgraph_host_security.py
security-contracts:
	@$(HATCH) run pytest -o addopts= tests/test_rendered_security.py tests/test_generated_security_defaults.py tests/test_generated_webhook_boundaries.py

.PHONY: lint-workflows
lint-workflows: ensure-hatch
	@$(HATCH) run python tools/lint_workflow_pins.py
	@$(HATCH) run python tools/lint_hatch_matrix.py

# `lint` already runs the type check (see [tool.hatch.envs.default.scripts]), so check is lint.
.PHONY: check
check: lint
	@echo "Lint and type check passed."

.PHONY: check-all
check-all: ensure-hatch
	@$(MAKE) check
	@$(MAKE) lint-workflows
	@$(MAKE) test
	@$(MAKE) security
	@echo "All checks passed including tests and security scan."

.PHONY: precommit
precommit: ensure-hatch
	@$(HATCH) run precommit

.PHONY: precommit-install
precommit-install: ensure-hatch
	@$(HATCH) run precommit-install

.PHONY: test
test: ensure-hatch
	@echo "Running tests..."
	@$(HATCH) run test

.PHONY: cov
cov: ensure-hatch
	@$(HATCH) run cov
	@echo "Open htmlcov/index.html in your browser to view the coverage report."
	@echo "coverage.xml generated for Codecov upload."

.PHONY: e2e-local
e2e-local: ensure-hatch
	@echo "Running e2e tests against local Azurite (E2E_BASE_URL=http://localhost:7071)..."
	@E2E_BASE_URL=http://localhost:7071 $(HATCH) run e2e-azure

.PHONY: e2e-azure
e2e-azure: ensure-hatch
	@echo "Running e2e tests against Azure (E2E_BASE_URL must be set)..."
	@$(HATCH) run e2e-azure

.PHONY: build
build: ensure-hatch
	@$(HATCH) build

.PHONY: publish-test
publish-test: ensure-hatch
	@$(HATCH) publish --repo test

.PHONY: version
version: ensure-hatch
	@echo "Current version:"
	@$(HATCH) version

.PHONY: docs
docs:
	@if [ -n "$$CI" ]; then \
		echo "CI detected: running MkDocs directly"; \
		pip install "mkdocs<2.0" "mkdocs-material<10.0" "mkdocstrings[python]<1.0" > /dev/null 2>&1; \
		mkdocs build; \
	else \
		$(MAKE) ensure-hatch > /dev/null; \
		$(HATCH) run mkdocs build; \
	fi

.PHONY: docs-serve
docs-serve: ensure-hatch
	@$(HATCH) run docs

.PHONY: doctor
doctor:
	@echo "Python version:" && $(PYTHON) --version
	@echo "Installed packages:" && $(HATCH) env run pip list || echo "No hatch environment found"
	@echo "Azure Function Core Tools version:" && func --version || echo "func not found"
	@echo "Pre-commit hook installed:"
	@if [ -f .git/hooks/pre-commit ]; then echo yes; else echo no; fi

.PHONY: clean
clean:
	@rm -rf *.egg-info dist build __pycache__ .pytest_cache

.PHONY: clean-all
clean-all: clean
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
	@rm -rf .mypy_cache .ruff_cache .pytest_cache .coverage coverage.xml htmlcov .DS_Store $(VENV_DIR) site

.PHONY: help
help:
	@echo "Available commands:" && \
	grep -E '^\.PHONY: ' Makefile | cut -d ':' -f2 | xargs -n1 echo "  - make"
