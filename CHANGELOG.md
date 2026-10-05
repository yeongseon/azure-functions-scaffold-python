# Changelog

All notable changes to this project will be documented in this file.
## [0.8.0](https://github.com/yeongseon/azure-functions-scaffold-python/compare/v0.7.3...v0.8.0) (2026-10-05)


### Features

* **templates:** emit requirements.txt in generated projects ([#374](https://github.com/yeongseon/azure-functions-scaffold-python/issues/374)) ([1f46475](https://github.com/yeongseon/azure-functions-scaffold-python/commit/1f4647567db3a4007963ebef6d25906e8a0f53cd))


### Bug Fixes

* **templates:** keep generated HTTP handlers indexable ([#372](https://github.com/yeongseon/azure-functions-scaffold-python/issues/372)) ([c650df7](https://github.com/yeongseon/azure-functions-scaffold-python/commit/c650df7666b1f0b279c7dfb7c3b8159d57e10534))

## [0.7.3](https://github.com/yeongseon/azure-functions-scaffold-python/compare/v0.7.2...v0.7.3) (2026-10-04)


### Bug Fixes

* **templates:** preserve worker indexing through logging decorators ([#366](https://github.com/yeongseon/azure-functions-scaffold-python/issues/366)) ([84ad182](https://github.com/yeongseon/azure-functions-scaffold-python/commit/84ad18255108c8fdc5df3481c87aed2b042915f1))

## [0.7.2](https://github.com/yeongseon/azure-functions-scaffold-python/compare/v0.7.1...v0.7.2) (2026-10-04)


### Bug Fixes

* **scaffold:** reject project names ending in a separator ([#363](https://github.com/yeongseon/azure-functions-scaffold-python/issues/363)) ([72e2211](https://github.com/yeongseon/azure-functions-scaffold-python/commit/72e221107a2f3c2c0b3357d814e7d33ff177ae13))
* **templates:** allow newer Python versions in generated projects ([#360](https://github.com/yeongseon/azure-functions-scaffold-python/issues/360)) ([f242924](https://github.com/yeongseon/azure-functions-scaffold-python/commit/f242924e5e0157847e99036d4f931585e21394a8))
* **templates:** declare the langgraph runtime dependency ([#359](https://github.com/yeongseon/azure-functions-scaffold-python/issues/359)) ([45bd74e](https://github.com/yeongseon/azure-functions-scaffold-python/commit/45bd74e7dbfc04f3f0dccfabd7cc6ae8c7d92bb9))
* **templates:** emit structured logs from generated projects ([#362](https://github.com/yeongseon/azure-functions-scaffold-python/issues/362)) ([a4025c2](https://github.com/yeongseon/azure-functions-scaffold-python/commit/a4025c218e76d27c7d0dd3a11c520633d862528b))
* **templates:** generate a valid durable function ([#357](https://github.com/yeongseon/azure-functions-scaffold-python/issues/357)) ([3ce04c7](https://github.com/yeongseon/azure-functions-scaffold-python/commit/3ce04c7c5863d59e40b448be9085958ef33dab36))
* **templates:** give each ai function its own route ([#361](https://github.com/yeongseon/azure-functions-scaffold-python/issues/361)) ([657a472](https://github.com/yeongseon/azure-functions-scaffold-python/commit/657a472150aade400efb30361ec0dce9fa96a08d))

## [0.7.1](https://github.com/yeongseon/azure-functions-scaffold-python/compare/v0.7.0...v0.7.1) (2026-10-02)


### Bug Fixes

* **generator:** list configuration updates only when content changes ([#346](https://github.com/yeongseon/azure-functions-scaffold-python/issues/346)) ([821baad](https://github.com/yeongseon/azure-functions-scaffold-python/commit/821baada1b2e76ed25cae175d8ec9cee49cef101))
* **generator:** report only files an add dry-run will create ([#343](https://github.com/yeongseon/azure-functions-scaffold-python/issues/343)) ([b49eb92](https://github.com/yeongseon/azure-functions-scaffold-python/commit/b49eb92513eb5a6ca1a776398426fb3f29da35c4))
* **scaffold:** reject blocked targets during dry-run ([#340](https://github.com/yeongseon/azure-functions-scaffold-python/issues/340)) ([765b06a](https://github.com/yeongseon/azure-functions-scaffold-python/commit/765b06a31afe9cfdcd518cdfeb63d7ae251773e9))
* **scaffold:** reject dangling destination symlinks ([#341](https://github.com/yeongseon/azure-functions-scaffold-python/issues/341)) ([108fa36](https://github.com/yeongseon/azure-functions-scaffold-python/commit/108fa36818a1047f966981e1d963c8e412820eca))

## [0.7.0](https://github.com/yeongseon/azure-functions-scaffold-python/compare/v0.6.6...v0.7.0) (2026-10-01)


### Bug Fixes

* **compat:** deprecate Python 3.10 ahead of its removal ([#322](https://github.com/yeongseon/azure-functions-scaffold-python/issues/322)) ([ca905ec](https://github.com/yeongseon/azure-functions-scaffold-python/commit/ca905ec7c4fa31a07dffed8da79610c7435cb08e))
* **generator:** report incomplete rollback ([#327](https://github.com/yeongseon/azure-functions-scaffold-python/issues/327)) ([a0158f7](https://github.com/yeongseon/azure-functions-scaffold-python/commit/a0158f75614516689f6e01df0df7f7a9d17d129f))
* **options:** keep the normalized Python version ([#325](https://github.com/yeongseon/azure-functions-scaffold-python/issues/325)) ([d4e61fc](https://github.com/yeongseon/azure-functions-scaffold-python/commit/d4e61fc191e53df1d689bc8c5fa9a92c420a1ee1))
* **scaffolder:** copy non-template files byte-for-byte ([#324](https://github.com/yeongseon/azure-functions-scaffold-python/issues/324)) ([4e3a11b](https://github.com/yeongseon/azure-functions-scaffold-python/commit/4e3a11b35983697e71355a715fdd26784aaf35ab))
* **scaffolder:** preserve existing project when overwrite generation fails ([#326](https://github.com/yeongseon/azure-functions-scaffold-python/issues/326)) ([251a9c9](https://github.com/yeongseon/azure-functions-scaffold-python/commit/251a9c9ea056c2bd72cf9ad1fbc3c814ca2c766a))
* **scaffolder:** reject unsupported template features in the Python API ([#323](https://github.com/yeongseon/azure-functions-scaffold-python/issues/323)) ([70003f2](https://github.com/yeongseon/azure-functions-scaffold-python/commit/70003f242ad9a7e058fea360b8d0f92811a12c85))
* **scaffold:** render planned templates during dry-run ([#328](https://github.com/yeongseon/azure-functions-scaffold-python/issues/328)) ([176f509](https://github.com/yeongseon/azure-functions-scaffold-python/commit/176f5092f32b9116ce44cb8b2d754839a04dd308))


### Miscellaneous Tasks

* release 0.7.0 ([5b6aef5](https://github.com/yeongseon/azure-functions-scaffold-python/commit/5b6aef5b8505fab991abca24fd8e251a766805b6))

## [0.6.6](https://github.com/yeongseon/azure-functions-scaffold-python/compare/v0.6.5...v0.6.6) (2026-09-29)


### Bug Fixes

* **ci:** correct release wording, stale.yml inputs, and add issue templates ([#301](https://github.com/yeongseon/azure-functions-scaffold-python/issues/301)) ([e753ea4](https://github.com/yeongseon/azure-functions-scaffold-python/commit/e753ea47ac28033c1d99a608ae78503c6bbab87e))
* **ci:** stop the format gate dropping type-changed Python paths ([#298](https://github.com/yeongseon/azure-functions-scaffold-python/issues/298)) ([f09d91c](https://github.com/yeongseon/azure-functions-scaffold-python/commit/f09d91ca5e694ee92c0be2646f3e0c1cd0851d5f))
* **options:** honor an explicitly empty tooling override (fixes [#288](https://github.com/yeongseon/azure-functions-scaffold-python/issues/288)) ([#289](https://github.com/yeongseon/azure-functions-scaffold-python/issues/289)) ([148cab2](https://github.com/yeongseon/azure-functions-scaffold-python/commit/148cab2b71541684850bf59fb8d1f4580437a4b2))


### Documentation

* align the contributor contract with the actual configuration ([#299](https://github.com/yeongseon/azure-functions-scaffold-python/issues/299)) ([8616286](https://github.com/yeongseon/azure-functions-scaffold-python/commit/86162864b02f126deaff542956d675d1454a0cf1))
* codify issue-based project management convention in AGENTS.md ([#267](https://github.com/yeongseon/azure-functions-scaffold-python/issues/267)) ([4a1049e](https://github.com/yeongseon/azure-functions-scaffold-python/commit/4a1049e43254db7f8c760ab511e8f1fb4d7dcdc4))


### Testing

* guard sibling-floor coverage of the minimum-resolution axis ([#257](https://github.com/yeongseon/azure-functions-scaffold-python/issues/257)) ([d27d1de](https://github.com/yeongseon/azure-functions-scaffold-python/commit/d27d1de49d2a3b8e1026286912eac72e0c1155ec)), closes [#256](https://github.com/yeongseon/azure-functions-scaffold-python/issues/256)


### Miscellaneous Tasks

* add hatch-matrix hygiene lint and guard ci-test matrix ([#273](https://github.com/yeongseon/azure-functions-scaffold-python/issues/273)) ([ec970bb](https://github.com/yeongseon/azure-functions-scaffold-python/commit/ec970bb39983d811a3eadc61289100feacf72e5a)), closes [#272](https://github.com/yeongseon/azure-functions-scaffold-python/issues/272)
* adopt release-please and gate PyPI on in-chain Azure e2e ([#309](https://github.com/yeongseon/azure-functions-scaffold-python/issues/309)) ([d383b97](https://github.com/yeongseon/azure-functions-scaffold-python/commit/d383b97c5b944820924f32f4e0326c211e6a4dfc))
* allow build/ branch prefix in branch-naming validation ([#279](https://github.com/yeongseon/azure-functions-scaffold-python/issues/279)) ([1424425](https://github.com/yeongseon/azure-functions-scaffold-python/commit/1424425f3985755ccff1df7f47bbc383b41b1752))
* **ci:** group dependabot updates + auto-merge patch/minor ([#255](https://github.com/yeongseon/azure-functions-scaffold-python/issues/255)) ([d8d08b7](https://github.com/yeongseon/azure-functions-scaffold-python/commit/d8d08b764e685ccb251740ae1ae4313e4194e7c2))
* **deps:** bump actions/download-artifact from 4.3.0 to 8.0.1 ([#241](https://github.com/yeongseon/azure-functions-scaffold-python/issues/241)) ([ea62e82](https://github.com/yeongseon/azure-functions-scaffold-python/commit/ea62e8242d007b5f20c5e5f1816dcb4c7bc1333a))
* **deps:** bump actions/upload-artifact from 4.6.2 to 7.0.1 ([#248](https://github.com/yeongseon/azure-functions-scaffold-python/issues/248)) ([812b861](https://github.com/yeongseon/azure-functions-scaffold-python/commit/812b8612f588e47d65afbe5094aca3cd1891a702))
* **deps:** bump anchore/sbom-action in the github-actions group ([#269](https://github.com/yeongseon/azure-functions-scaffold-python/issues/269)) ([4ffe6b7](https://github.com/yeongseon/azure-functions-scaffold-python/commit/4ffe6b75e83a89e2e0a948353e040c9dd8b1f32a))
* **deps:** bump azure-functions-doctor from 0.19.0 to 0.19.2 ([#254](https://github.com/yeongseon/azure-functions-scaffold-python/issues/254)) ([00316bb](https://github.com/yeongseon/azure-functions-scaffold-python/commit/00316bbde576ea5ab481381b353476850de5f138))
* **deps:** bump azure-functions-logging from 0.10.0 to 0.10.2 ([#253](https://github.com/yeongseon/azure-functions-scaffold-python/issues/253)) ([39b0c32](https://github.com/yeongseon/azure-functions-scaffold-python/commit/39b0c328082b34074bd7ff9e6201d336d97d2132))
* **deps:** bump azure-functions-openapi ([#264](https://github.com/yeongseon/azure-functions-scaffold-python/issues/264)) ([d83c322](https://github.com/yeongseon/azure-functions-scaffold-python/commit/d83c322a05d74fe07adbc15ad7161eb30f11163f))
* **deps:** bump azure-functions-openapi from 0.21.0 to 0.21.2 ([#250](https://github.com/yeongseon/azure-functions-scaffold-python/issues/250)) ([d516591](https://github.com/yeongseon/azure-functions-scaffold-python/commit/d5165911167aba225f5abe828c34d5d7d6715427))
* **deps:** bump azure-functions-validation from 0.10.0 to 0.11.2 ([#249](https://github.com/yeongseon/azure-functions-scaffold-python/issues/249)) ([70796e0](https://github.com/yeongseon/azure-functions-scaffold-python/commit/70796e010ca73ca22e6343b19c7ae1219aebf9e8))
* **deps:** bump codecov/codecov-action in the github-actions group ([#283](https://github.com/yeongseon/azure-functions-scaffold-python/issues/283)) ([070307f](https://github.com/yeongseon/azure-functions-scaffold-python/commit/070307f516f68eaa5da7f9aed0293cb58d765ae1))
* **deps:** bump dependabot/fetch-metadata from 2.5.0 to 3.1.0 ([#260](https://github.com/yeongseon/azure-functions-scaffold-python/issues/260)) ([8af1a94](https://github.com/yeongseon/azure-functions-scaffold-python/commit/8af1a94f8baa05b6d88664fd0f6cccf4b81511f7))
* **deps:** bump github/codeql-action/analyze from 4.37.6 to 4.37.7 ([#247](https://github.com/yeongseon/azure-functions-scaffold-python/issues/247)) ([98d9461](https://github.com/yeongseon/azure-functions-scaffold-python/commit/98d9461d33ea5da86c052e78fbcbc71145bbafe0))
* **deps:** bump github/codeql-action/init from 4.37.6 to 4.37.7 ([#246](https://github.com/yeongseon/azure-functions-scaffold-python/issues/246)) ([03ef4a4](https://github.com/yeongseon/azure-functions-scaffold-python/commit/03ef4a4457a8c0060d9f55a009f730a55c5f1513))
* **deps:** bump mypy from 2.3.0 to 2.3.1 ([#251](https://github.com/yeongseon/azure-functions-scaffold-python/issues/251)) ([4d97541](https://github.com/yeongseon/azure-functions-scaffold-python/commit/4d97541d40161483a8168d8a824c302e8bbe1ce1))
* **deps:** bump ruff from 0.16.2 to 0.16.3 ([#252](https://github.com/yeongseon/azure-functions-scaffold-python/issues/252)) ([88345ea](https://github.com/yeongseon/azure-functions-scaffold-python/commit/88345ea68477530e334ca1171b3656149ab1af93))
* **deps:** bump ruff in the python-dependencies group ([#282](https://github.com/yeongseon/azure-functions-scaffold-python/issues/282)) ([5b98121](https://github.com/yeongseon/azure-functions-scaffold-python/commit/5b98121a665f3b29b0121eff3d8586deb3ff204c))
* **deps:** bump the github-actions group with 2 updates ([#259](https://github.com/yeongseon/azure-functions-scaffold-python/issues/259)) ([2b2ce4f](https://github.com/yeongseon/azure-functions-scaffold-python/commit/2b2ce4fb9c372cd3d0cff6b189c9a8798dcaa2c6))
* **deps:** bump the github-actions group with 2 updates ([#296](https://github.com/yeongseon/azure-functions-scaffold-python/issues/296)) ([bfb81d3](https://github.com/yeongseon/azure-functions-scaffold-python/commit/bfb81d3efc373e1330aca93ae771e827402a1515))
* **deps:** bump the github-actions group with 3 updates ([#281](https://github.com/yeongseon/azure-functions-scaffold-python/issues/281)) ([174b804](https://github.com/yeongseon/azure-functions-scaffold-python/commit/174b8047b5a757feb76b7cb9837427be361ebedf))
* **deps:** bump the github-actions group with 4 updates ([#265](https://github.com/yeongseon/azure-functions-scaffold-python/issues/265)) ([a8a774b](https://github.com/yeongseon/azure-functions-scaffold-python/commit/a8a774b7c252728073decb2f3b2b3b685c5b41a5))
* **deps:** bump the python-dependencies group with 3 updates ([#268](https://github.com/yeongseon/azure-functions-scaffold-python/issues/268)) ([c4012f8](https://github.com/yeongseon/azure-functions-scaffold-python/commit/c4012f898989b7969d0499627e142e2101f690e5))
* **deps:** bump the python-dependencies group with 4 updates ([#280](https://github.com/yeongseon/azure-functions-scaffold-python/issues/280)) ([a13d1c1](https://github.com/yeongseon/azure-functions-scaffold-python/commit/a13d1c17896c8a33ce1173090b22bc16fd361e3b))
* **deps:** bump the python-dependencies group with 5 updates ([#258](https://github.com/yeongseon/azure-functions-scaffold-python/issues/258)) ([4c986df](https://github.com/yeongseon/azure-functions-scaffold-python/commit/4c986df825840d546313e9290c1fce7107948617))
* enforce Ruff formatting in PR quality checks ([#294](https://github.com/yeongseon/azure-functions-scaffold-python/issues/294)) ([aac3ecd](https://github.com/yeongseon/azure-functions-scaffold-python/commit/aac3ecd3f94393df64d8d6410243d9528c3696ea))
* ignore uv.lock ([#305](https://github.com/yeongseon/azure-functions-scaffold-python/issues/305)) ([041a912](https://github.com/yeongseon/azure-functions-scaffold-python/commit/041a9122287c50859c4bcfd2ff8af2133fd96e27)), closes [#304](https://github.com/yeongseon/azure-functions-scaffold-python/issues/304)
* modernize typing and pin ruff, complete AGENTS.md, unify Azure e2e auth ([#307](https://github.com/yeongseon/azure-functions-scaffold-python/issues/307)) ([457946d](https://github.com/yeongseon/azure-functions-scaffold-python/commit/457946de7a04d9efe5c442faef1e770031fad294))
* run tests on the real matrix interpreter + fix webhook template for openapi 0.24 ([#276](https://github.com/yeongseon/azure-functions-scaffold-python/issues/276)) ([da78fbb](https://github.com/yeongseon/azure-functions-scaffold-python/commit/da78fbb1ab30b52d73734c3c9c76a3dcbdd8d07d)), closes [#278](https://github.com/yeongseon/azure-functions-scaffold-python/issues/278)


### Other

* **deps:** add Dependabot cooldown to age new releases ([#271](https://github.com/yeongseon/azure-functions-scaffold-python/issues/271)) ([3b6473f](https://github.com/yeongseon/azure-functions-scaffold-python/commit/3b6473f7ed0e34cf9772020b9ec17e5dd09c8995)), closes [#262](https://github.com/yeongseon/azure-functions-scaffold-python/issues/262)

## [0.6.5] - 2026-08-14

### Bug Fixes

- *(e2e)* Probe existing /api/health route instead of nonexistent /api/hello (#227) 

### Documentation

- Consolidate official documentation URL onto yeongseon.dev (#237) 
- *(i18n)* Adopt best-effort translation policy with staleness banners (#230) 
- Fix template drift in example and guide docs (#231) 
- Align http-template docs with health+webhooks structure (#228) 
- *(reference)* Document include_azd and fix deprecated afs add flow (#220) 

### Features

- *(packages)* Raise a descriptive error for unknown requirement() names (#238) 

### Miscellaneous Tasks

- Stop auto-deploying docs to GitHub Pages (#240) 
- *(ci)* Normalize action version-comment labels (#235) 
- Add workflow pin-hygiene lint (#233) 
- Use ref-based OIDC subject for e2e-azure (#226) 
- Gate PyPI publish behind lib-tests + real-Azure certification (#222) 
- Ignore agent orchestration state (.omc/) (#224) 
- Bump ruff to 0.16.2 and repair pre-commit hooks (#217) 

### Other

- Bump version to 0.6.5 
## [0.6.4] - 2026-08-11

### Documentation

- Update changelog 
- Add Branch Hygiene section to AGENTS.md 
- Fix broken doc links to unblock strict mkdocs build 
- *(release)* Require cookbook dogfood verification after publish 

### Miscellaneous Tasks

- *(deps)* Bump ruff from 0.16.0 to 0.16.1 (#205) 
- *(deps)* Bump azure/login from 3.0.0 to 3.0.1 (#204) 
- *(deps)* Sync package catalog + tests to bumped sibling floors 
- *(deps)* Bump sibling toolkit floors to latest releases 
- *(ci)* Replace || true with exit-code-aware doctor assertion in smoke tests (#203) 
- *(codeql)* Bump codeql-action init+analyze to v4.37.6 together 

### Other

- Bump version to 0.6.4 
## [0.6.3] - 2026-08-09

### Documentation

- Update changelog 
- Require translation sync in the same PR as English changes (Closes #183) (#184) 
- Correct azure-functions-db description in ecosystem table (#182) 
- Add per-template generated-output examples (#174) 
- *(readme)* Fix broken Release badge to publish-pypi.yml (#167) 

### Miscellaneous Tasks

- *(deps)* Cap azure-functions below 2.0.0 (#216) 
- Run doctor in scaffold template smoke tests (#199) 
- Add min-vs-latest dependency test matrix (#200) 
- *(deps)* Bump codeql-action init+analyze to 4.37.4 atomically 
- *(deps)* Bump actions/stale from 10.4.0 to 11.0.0 (#193) 
- Track issue priority via priority:* labels instead of body line (#194) 
- *(deps)* Bump github/codeql-action/init from 4.37.1 to 4.37.3 (#189) 
- *(deps)* Bump actions/checkout from 7.0.0 to 7.0.1 (#187) 
- *(deps)* Bump ruff from 0.15.22 to 0.16.0 (#186) 
- *(deps)* Bump actions/setup-python from 6.3.0 to 7.0.0 (#185) 
- *(generator)* Decompose generator into focused package (#179) 
- *(deps)* Bump github/codeql-action/analyze from 4.37.0 to 4.37.1 (#171) 
- *(deps)* Bump github/codeql-action/init from 4.37.0 to 4.37.1 (#169) 
- *(deps)* Bump mypy from 2.2.0 to 2.3.0 (#170) 
- *(deps)* Bump actions/setup-node from 6.4.0 to 7.0.0 (#172) 
- *(deps)* Bump ruff from 0.15.21 to 0.15.22 (#173) 

### Other

- Bump version to 0.6.3 

### Refactor

- *(templates)* Centralize supported-package version catalog (#198) 
- *(generator)* Unify dry-run via dry_run param on add_* functions (#180) 
- *(cli)* Dedupe overlapping add-* commands via shared cli_common helpers (#178) 
- *(generator)* Extract inline function templates to Jinja partials (#177) 
- *(cli)* Generate worker commands from INTENT_SPECS table (#163) (#176) 
- *(generator)* Drop dead legacy write-path helpers (#163) (#175) 
- *(scaffold)* Fix cosmosdb template at source, drop normalize patch (#168) 
## [0.6.2] - 2026-07-18

### Bug Fixes

- *(ci)* Normalize e2e-azure OIDC subject via environment declaration (#123) 
- *(ci)* Replace fragile apt install of Core Tools with pinned npm (#126) 
- *(ci)* Remove obsolete --template option from e2e workflow 
- *(ci)* Correct CLI entrypoint name in e2e workflow 

### Documentation

- Update changelog 
- *(cli)* Align CLI reference with implemented commands and fix changelog/migration drift (#160) 
- *(diagram)* Portable classDiagram notation and i18n README flowchart parity (#161) 
- Add discoverability metadata (pepy badge + llms.txt) (#166) 
- Document Release Process in AGENTS.md (#154) 
- *(readme)* Document all 9 ADDABLE_TRIGGERS across en/ko/ja/zh-CN (#145) 
- *(stacks)* Restructure --profile examples for current CLI surface (#141) 
- *(reference)* Remove stale --interactive flag from cli.md (#139) 
- *(cli)* Update stale top-level afs new examples after CLI surface change (#127) 

### Miscellaneous Tasks

- *(deps)* Bump github/codeql-action/analyze from 4.36.2 to 4.37.0 (#149) 
- *(deps)* Bump github/codeql-action/init from 4.36.2 to 4.37.0 (#148) 
- *(deps)* Bump actions/stale from 10.3.0 to 10.4.0 (#150) 
- *(deps)* Bump ruff from 0.15.20 to 0.15.21 (#151) 
- *(deps)* Bump mypy from 2.1.0 to 2.2.0 (#152) 
- *(deps)* Bump actions/checkout from 6.0.2 to 7.0.0 (#134) 
- *(deps)* Bump actions/setup-python from 6.2.0 to 6.3.0 (#136) 
- *(deps)* Bump ruff from 0.15.16 to 0.15.20 (#137) 
- *(repo)* Harden gitignore and document generated artifacts (#124) 
- *(deps)* Bump codecov/codecov-action from 6.0.1 to 7.0.0 (#132) 
- *(ci)* Standardize Action pinning to immutable SHAs (#125) 
- *(deps)* Bump ruff from 0.15.12 to 0.15.16 (#122) 
- *(deps)* Bump github/codeql-action from 4.35.4 to 4.36.2 (#121) 
- *(deps)* Bump actions/stale from 10.2.0 to 10.3.0 (#118) 
- *(deps)* Bump codecov/codecov-action from 6.0.0 to 6.0.1 (#116) 
- *(deps)* Bump mypy from 2.0.0 to 2.1.0 (#110) 

### Other

- Bump version to 0.6.2 

### Refactor

- *(generator)* Co-locate allowed features on TemplateSpec (#164) 

### Testing

- Correct Codecov version comment and bound generated-project smoke tests (#162) 
- *(docs)* Broaden cli-example smoke test to accept azure-functions-scaffold alias (#142) 
## [0.6.1] - 2026-05-14

### Documentation

- Update changelog 
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
