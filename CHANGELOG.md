# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed (BREAKING - packaging)

- Renamed PyPI package from `azure-functions-scaffold-python` to `azure-functions-scaffold` to align with the existing PyPI registration (the suffixed name was never published). Install command: `pip install azure-functions-scaffold`. The CLI binary `afs` and the long-form `azure-functions-scaffold` are unchanged behaviorally; the long-form name no longer carries the `-python` suffix.
- Generated project templates now depend on unsuffixed sibling packages: `azure-functions-logging`, `azure-functions-openapi`, `azure-functions-validation`, `azure-functions-doctor`, `azure-functions-db`. Existing `-python`-suffixed deps were unresolvable on PyPI.
- Function-app marker comments are now `# azure-functions-scaffold: function imports` / `# azure-functions-scaffold: function registrations` (was `azure-functions-scaffold-python: ...`). Existing scaffolded projects will continue to work because the generator still recognizes both legacy and new markers - see migration notes.

### Migration

- Users with previously-scaffolded projects do not need to take action; the marker constants only matter when running `afs api add` / `afs advanced add` / `afs api add-route` / `afs api add-resource` against an existing project. If those commands fail with "marker not found" against an old scaffold, replace the comment in `function_app.py` from `# azure-functions-scaffold-python:` to `# azure-functions-scaffold:`.
- Users following the previous suffixed install instructions will hit a 404. The README and docs are updated; PyPI package name is now `azure-functions-scaffold`.

### Fixed

- Generated projects' `pytest` invocation no longer fails with `ModuleNotFoundError` for `app.*` imports. Templates now ship `pythonpath = ["."]` in `[tool.pytest.ini_options]`, which pytest 8+ requires when test files live as siblings to the package root (no `tests/__init__.py` convention).

## [0.5.0] - 2025-04-09

### Features

- Add `--with-db/--no-db` CLI flag with interactive prompt support
- Add `langgraph` template with LangGraphApp, echo agent, and full project structure
- Add `db-api` profile (http + strict preset + db + openapi + validation + doctor)
- Add `db_items` blueprint template (GET/POST /items) for database showcase
- Conditional `azure-functions-db-python[postgres]` dependency in generated pyproject.toml
- Conditional `DB_URL` in generated local.settings.json.example

### Testing

- Add tests for `--with-db` flag, langgraph template, and db-api profile (178 pass, 97% coverage)

## [0.4.0] - 2025-03-17

### Bug Fixes

- Resolve MkDocs strict-mode failures for nav and links (#38) (#39) 
- Align terminology with Oracle review 
- Switch Mermaid fence format to fence_div_format for rendering 
- Guard git init error handling when stderr is missing (#19) 

### Documentation

- Add llms.txt for LLM-friendly documentation (#40) (#41) 
- Rewrite deployment guide for developer-friendly Azure Functions experience 
- Add deployment guide for scaffold CLI and generated projects (#35) 
- Fix stale diagrams in architecture.md (#34) 
- Add ecosystem positioning and design principle 
- Pin Mermaid JS version and add site_url 
- Add missing standard sections and fix stale content in architecture doc (#26) 
- Add architecture diagram, MS Learn sources, and cross-repo See Also links (#24) 

### Features

- Add --azd flag, --profile option, and profiles command to CLI 
- Add azd support to scaffolder context and rendering 
- Add profile registry and azd support to template registry 
- Add ProfileSpec model for project profile bundles 

### Miscellaneous Tasks

- *(deps)* Bump mypy from 1.19.1 to 1.20.0 
- *(deps)* Bump ruff from 0.15.8 to 0.15.9 
- *(deps)* Bump codecov/codecov-action from 5.5.3 to 6.0.0 (#15) 
- *(deps)* Bump ruff from 0.15.6 to 0.15.8 (#16) 
- *(deps)* Bump anchore/sbom-action from 0.23.1 to 0.24.0 (#11) 
- *(deps)* Bump github/codeql-action from 4.33.0 to 4.35.1 (#17) 
- Use standard pypi environment name for Trusted Publisher 
- Rename publish environment from production to release 
- Unify CI/CD workflow configurations 

### Other

- Bump version to 0.4.0 

### Testing

- Update version assertion to 0.4.0 for upcoming release 
- Add tests for azd flag, profile system, and profile registry 

### Bug Fixes

- Generate requirements.txt from pyproject.toml before func publish, add startup probe 
- Fix scaffold e2e - correct warmup route, pyproject.toml check, cleanup resilience 
- Update e2e workflow to use correct scaffold CLI 'new' command 
- Add --no-cov and pytest-html artifact to e2e workflow 

### Documentation

- Add mermaid diagrams to architecture and README 
- Add mermaid support to mkdocs configuration 
- Add real Azure e2e test section to testing.md and CHANGELOG 
- Document azure-functions-logging-python as built-in default 

### Features

- Add real Azure e2e tests and CI workflow 
- Add eventhub, cosmosdb, durable, and ai scaffold templates 

### Miscellaneous Tasks

- Release v0.3.2 
- Standardize .gitignore format (#5) 
- Fix repo consistency issues (LICENSE, ruff version, coverage threshold, sdist paths, pre-commit, codecov, SBOM, CodeQL) (#4) 
- *(deps)* Update mkdocstrings[python] requirement from <1.0 to <2.0 (#1) 
- *(deps)* Bump anchore/sbom-action from 0.23.0 to 0.23.1 (#2) 
- *(deps)* Bump ruff from 0.15.5 to 0.15.6 (#3) 
- Trigger e2e only on release tag push (v*) 
- Upgrade GitHub Actions to Node.js 24 compatible versions 
- Enforce coverage fail_under = 92 
- Add keywords to pyproject.toml 
- Add AGENTS.md, Typing classifier, test_public_api, Dev Status 4-Beta, .venv-review in .gitignore 
- Unify CI workflow comments with canonical validation repo 
- Fix release.yml - correct pypi-publish action ref and unify environment to production 

### Testing

- Add generator coverage tests to reach 92% threshold 

### Bug Fixes

- Add root index.md to resolve docs site 404 
- Resolve Ruff I001 import sorting error in generated function_app.py 
- Harden generator and scaffolder against edge cases 
- Resolve Jinja2 template whitespace for ruff compliance 
- Correct Service Bus get_body() usage, CI codecov failure, and variable shadowing 

### Documentation

- Overhaul documentation to production quality 
- Sync translated READMEs (ko, ja, zh-CN) with English 
- Unify README — Title Case H1, add Why Use It/Scope/Features/Installation sections, update Ecosystem format, reorder sections 
- Add example-first design section to PRD 
- Add end-to-end tutorials for all 5 function templates 
- Restructure documentation and add ruff format config 
- Add generated code examples across documentation 
- Elevate scaffold documentation to production quality 
- Add badges and translated READMEs (ko, ja, zh-CN) 
- Update CHANGELOG, README, and roadmap for v0.3.0 
- Update CHANGELOG with all trigger types and add CHANGELOG.md to forbid-korean hook 
- *(readme)* Move disclaimer before license section 
- *(readme)* Add Microsoft trademark disclaimer 
- Document scaffold presets and function generation 

### Features

- Add --with-doctor flag and conditional Makefile target 
- Integrate azure-functions-logging-python into all scaffold templates 
- Add --with-openapi and --with-validation flags to new command 
- Add explicit overwrite support for project generation 
- Validate interactive scaffold choices before generation 
- Add dry-run previews for scaffold generation and function additions 
- Feat: 
- Feat: 
- Feat: 
- Support interactive tooling selection 
- Add interactive scaffolding and function generation 

### Miscellaneous Tasks

- Update pre-commit hook versions and unify forbid-korean targets 
- Use trusted publishing for scaffold releases 
- Support manual scaffold releases 
- Chore: 
- Align scaffold release and docs structure 
- Chore: 

### Other

- Bump version to 0.3.1 

### Refactor

- Tighten scaffold contracts and shared metadata 

### Styling

- Unify tooling — remove black, standardize pre-commit and Makefile 

### Testing

- Update tests for v0.3.0 logging and doctor features 
- Expand scaffold e2e coverage for simple trigger templates 
- Test: 
<!-- generated by git-cliff -->
