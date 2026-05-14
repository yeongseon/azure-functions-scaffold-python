# Changelog

All notable changes to this project will be documented in this file.
## [0.6.1] - 2026-05-14

### Documentation

- Fix ecosystem table names, badges, and Part of intro line 
- Mark cookbook as dogfood, fix ecosystem table description 

### Miscellaneous Tasks

- *(deps)* Bump mypy from 1.20.2 to 2.0.0 
- *(deps)* Bump actions/checkout from 4 to 6 
- *(deps)* Bump actions/setup-python from 5 to 6 
- *(deps)* Bump github/codeql-action from 4.35.2 to 4.35.4 
- *(release)* Fix changelog template and decouple version test from literals 

### Other

- Bump version to 0.6.1 

### Testing

- Raise coverage to 95%+ and enforce via AGENTS.md and pyproject.toml 
## [0.6.0] - 2026-04-30

### Bug Fixes

- *(templates)* Correct langgraph template strict mypy errors (#100) 
- *(templates)* Correct azure-functions-openapi API usage in http template (#99) 
- *(templates)* Correct durable Functions imports and types (#98) 
- *(templates)* Order imports per PEP 8 in route and langgraph templates (#97) 
- *(generator)* Sort app.functions imports after marker-based insertion (#96) 
- *(generator)* Split ADDABLE_TRIGGERS from SUPPORTED_TRIGGERS (#84) 
- *(scaffold)* Guard --overwrite with TTY confirmation and .git check (#89) 
- *(templates)* Add pythonpath to generated pytest config (#93) 
- *(templates)* Default to AuthLevel.FUNCTION and require WEBHOOK_SECRET (#83) 
- *(generator)* Reject Python keywords and invalid identifiers in function names (#82) 
- *(generator)* Make add_function/add_resource/add_route atomic (#85) 
- *(generator)* Align function_app.py marker constants with templates (#81) 
- *(cli)* Validate advanced new flag/template compatibility (#88) 
- *(cli)* Add deprecation shims for legacy 'add' and 'profiles' (#87) 
- *(cli)* Print help when invoked with no subcommand (#86) 
- *(packaging)* Align PyPI name with publish reality (drop -python suffix) (#90) 
- Align hatch wheel packages and toolkit dependency names (#70) 

### Documentation

- *(readme)* Add afs new vs func init comparison table (#92) 
- *(migration)* Draft 0.6.0 migration guide (#95) 
- *(cli)* Flag Python 3.14 as Preview on Azure Functions (#91) 
- *(agents)* Add Issue Conventions section to AGENTS.md 

### Miscellaneous Tasks

- Add generated-project smoke E2E for every template (#94) 
- *(deps)* Bump github/codeql-action from 4.35.1 to 4.35.2 (#67) 
- *(deps)* Bump ruff from 0.15.10 to 0.15.12 (#73) 
- *(deps)* Bump mypy from 1.20.0 to 1.20.2 (#72) 

### Release

- 0.6.0 (#102) 
## [0.5.1] - 2026-04-17

### Documentation

- Add example walkthroughs for all remaining templates (#64) 
- Add blessed package stacks guide 
- Standardize ecosystem table in README 

### Features

- Add orjson as default dependency for faster JSON serialization (#66) 
- Replace default users CRUD example with webhook receiver (#61) 
- Add structured logging and fix Oracle-identified bugs (#58) (#59) 
- Add top-level afs new alias and README front door redesign (#57) 
- Add route/resource engine — Jinja partials, generator, CLI commands, tests (#56) 
- Restructure HTTP template — replace hello endpoint with health+users CRUD (#55) 
- Intent-centric CLI redesign — replace profiles with intent commands (#48) 

### Miscellaneous Tasks

- *(deps)* Bump actions/upload-artifact from 7.0.0 to 7.0.1 
- *(deps)* Bump actions/github-script from 8.0.0 to 9.0.0 
- Update repo references for azure-functions-{feature}-python naming convention 
- Polish templates — fix sdist paths, update deps, enrich DX (#50) (#51) 
- Bump ruff from 0.15.9 to 0.15.10 (#46) 
## [0.5.0] - 2026-04-09

### Features

- Add --with-db flag, langgraph template, and db-api profile 

### Other

- Bump version to 0.5.0 
## [0.4.0] - 2026-04-08

### Bug Fixes

- Resolve MkDocs strict-mode failures for nav and links (#38) (#39) 
- Align terminology with Oracle review 
- Switch Mermaid fence format to fence_div_format for rendering 
- Guard git init error handling when stderr is missing (#19) 

### Documentation

- Update changelog 
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
## [0.3.2] - 2026-03-21

### Bug Fixes

- Generate requirements.txt from pyproject.toml before func publish, add startup probe 
- Fix scaffold e2e - correct warmup route, pyproject.toml check, cleanup resilience 
- Update e2e workflow to use correct scaffold CLI 'new' command 
- Add --no-cov and pytest-html artifact to e2e workflow 

### Documentation

- Add mermaid diagrams to architecture and README 
- Add mermaid support to mkdocs configuration 
- Add real Azure e2e test section to testing.md and CHANGELOG 
- Document azure-functions-logging as built-in default 

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
## [0.3.1] - 2026-03-14

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
- Integrate azure-functions-logging into all scaffold templates 
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
## [0.1.0] - 2026-03-07
<!-- generated by git-cliff -->
