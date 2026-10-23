VENV_DIR := .venv
PYTHON ?= python
HATCH ?= hatch
ifeq ($(CI),)
RUN := $(HATCH) run python
else
RUN := $(PYTHON)
endif

.PHONY: bootstrap ensure-hatch install install-ci shell reset hatch-clean
bootstrap ensure-hatch:
	@command -v $(HATCH) >/dev/null || { echo "Install Hatch once in an isolated tool environment"; exit 1; }
install: ensure-hatch
	@$(HATCH) env create
	@if [ -z "$$CI" ]; then $(MAKE) precommit-install; fi
install-ci:
	@$(PYTHON) -m pip install -e ".[dev,docs]"
shell: ensure-hatch
	@$(HATCH) shell
reset: clean-all install
hatch-clean: ensure-hatch
	@$(HATCH) env remove

.PHONY: format format-check style lint typecheck security lint-workflows check check-all
format:
	@$(RUN) -m ruff format src tests tools docs_hooks
format-check:
	@$(RUN) -m ruff format --check src tests tools docs_hooks
style: format-check
	@$(RUN) -m ruff check src tests tools docs_hooks
lint: style typecheck
typecheck:
	@$(RUN) -m mypy src tests tools/verification*.py
security:
	@$(RUN) -m bandit -r src
lint-workflows:
	@$(RUN) -m tools.lint_release_workflows
	@$(RUN) tools/lint_workflow_pins.py
	@$(RUN) tools/lint_hatch_matrix.py
check:
	@$(RUN) -m tools.verification quality
.PHONY: check-steps
check-steps: style typecheck security lint-workflows
check-all: verify

.PHONY: test integration verify report clean generated-project host-smoke wheel-smoke
test integration verify generated-project host-smoke wheel-smoke:
	@$(RUN) -m tools.verification $@
.PHONY: doctor
MAINTENANCE_PYTHON ?= $(shell command -v python3.11 || command -v python3)
doctor report clean:
	@environment=$$($(HATCH) env find 2>/dev/null); \
	if [ -x "$$environment/bin/python" ]; then interpreter="$$environment/bin/python"; \
	elif [ -n "$$VIRTUAL_ENV" ] && [ -x "$$VIRTUAL_ENV/bin/python" ]; then interpreter="$$VIRTUAL_ENV/bin/python"; \
	else interpreter="$(MAINTENANCE_PYTHON)"; fi; \
	"$$interpreter" -m tools.verification_maintenance $@

.PHONY: cov e2e-local e2e-azure build docs docs-serve
cov:
	@$(RUN) -m tools.verification test --cov-report=html:test-results/test/htmlcov
e2e-local: host-smoke
e2e-azure:
	@$(RUN) -m tools.verification azure-e2e
build:
	@$(RUN) -m tools.verification focused build -m build
docs:
	@$(RUN) -m tools.verification focused docs -m mkdocs build --strict
docs-serve:
	@$(RUN) -m mkdocs serve

.PHONY: precommit precommit-install publish-test version clean-all help
precommit precommit-install: ensure-hatch
	@$(HATCH) run $@
publish-test: ensure-hatch
	@$(HATCH) publish --repo test
version: ensure-hatch
	@$(HATCH) version
clean-all: clean
	@find . -type d -name "__pycache__" -not -path "./.git/*" -exec rm -rf {} +
	@find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -not -path "./.git/*" -delete
	@rm -rf .DS_Store $(VENV_DIR)
help:
	@echo "Canonical: install install-ci doctor format format-check check test integration verify e2e-azure report clean"
	@echo "check-all: exact alias of verify; focused commands produce PARTIAL evidence"
