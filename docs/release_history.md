# Release History and Provenance

This page records how each published version of **azure-functions-scaffold** maps to a Git tag, a
GitHub Release and a PyPI distribution, and lists the historical cases where those records do not
line up. The data was reconciled against Git, PyPI and GitHub on 2026-11-10. For how new versions
are released, see [Release Process](release_process.md).

---

## What each record proves

| Record | Proves | Does not prove |
|---|---|---|
| PyPI distribution | The package users install exists, with its files and upload time | Which commit built it (only PyPI attestations say so; all 15 versions have one) |
| Git tag | A commit was labelled with a version | That the tagged source is what shipped, or that anything was published |
| GitHub Release | A release page with notes exists | That a package was published |

A GitHub Release is never evidence of publication. Check the
[PyPI release history](https://pypi.org/project/azure-functions-scaffold/#history).

---

## Reconciliation summary

| Evidence set | Count |
|---|---:|
| Git tags | 21 |
| PyPI versions (`0.3.2` to `0.9.1`) | 15 |
| GitHub Releases | 18 |

| Category | Versions |
|---|---|
| Published, with a matching tag and GitHub Release | 13 versions: every published version except the two below |
| Published, tag exists, GitHub Release added afterwards | `0.4.0`, `0.5.0` |
| Unpublished release candidate: tag and GitHub Release, never on PyPI | `0.5.1`, `0.7.2`, `0.9.0` |
| Failed publish: tag only, no GitHub Release | `0.1.0`, `0.3.0`, `0.3.1` |

For every published version the package files on PyPI are byte-identical to the tagged commit, and
the PyPI attestation records a build from that tag at that commit (see
[How this was verified](#how-this-was-verified)).

---

## v0.9.0: unpublished, superseded by v0.9.1

The failure is recorded in issue
[#379](https://github.com/yeongseon/azure-functions-scaffold-python/issues/379); the fix is #380.

| Time (UTC) | Event |
|---|---|
| 02:24:41 | tag `v0.9.0` (commit `c892ee0`, which declares `0.9.0`) created; Release published |
| 02:24:42 | [`Publish to PyPI` run 37561849040](https://github.com/yeongseon/azure-functions-scaffold-python/actions/runs/37561849040) starts |
| 02:28:39 | the run ends as failed; `publish` was skipped |
| 02:37:26 | tag `v0.9.1` (commit `7f28568`, which includes the fix `938d82f`) created; Release published |
| 02:43:29 | `0.9.1` uploaded to PyPI |

**Facts.** In the run, *Build & verify version* and *Library tests* succeeded. In the *Azure
release certification* job the step *Run scaffold structure tests (no Azure)* failed. The job log
shows the cause: the step ran `pytest tests/e2e -v -k "scaffolded" --no-cov`, but the job installs
only the candidate wheel and pytest, so the `addopts` of `pyproject.toml` (`--cov=...`) reached a
pytest without `pytest-cov`:
`pytest: error: unrecognized arguments: --cov=src/azure_functions_scaffold --cov-report=xml --cov-report=term-missing --no-cov`,
exit code 4. This was a defect in the certification step, not in the package.

`v0.9.0` is an ancestor of `v0.9.1`, and the only commits between them are the fix and the release
commit, so every change in `0.9.0` shipped in `0.9.1`. No `0.9.0` distribution exists anywhere:
PyPI has no such version, TestPyPI has no project of this name, the failed run uploaded no
artifact and the Release has no assets. README and docs do not claim `0.9.0` is installable.
`CHANGELOG.md` has a `0.9.0` section because Release Please writes it when the tag is cut; it is
not edited.

**Decision**

- The tag and the Release are kept; nothing is moved, deleted or re-uploaded. The Release body now
  opens with a notice that `0.9.0` was not published and points to `0.9.1`; the notice is a
  protected statement in `.github/release-notes.json`.
- **Retry criteria.** Re-running a tag is only for a transient or environmental failure. A
  `workflow_dispatch` runs the workflow file at the tag, so it cannot pick up a correction made on
  `main`. This failure was a defect in the workflow as it stood at the tag, so fixing forward,
  which is what shipped `0.9.1`, was the only path. Never move a tag or upload an altered artifact
  under a consumed version.

---

## v0.7.2: unpublished, superseded by v0.7.3

The failure is recorded in issue
[#365](https://github.com/yeongseon/azure-functions-scaffold-python/issues/365). The Release
already carried a notice that it was not published; it is kept as a protected statement.

| Time (UTC) | Event |
|---|---|
| 13:29:43 | tag `v0.7.2` (commit `5011d56`, which declares `0.7.2`) created; Release published |
| 13:29:44 | [`Publish to PyPI` run 37205813473](https://github.com/yeongseon/azure-functions-scaffold-python/actions/runs/37205813473) starts |
| 13:51:17 | the run ends as failed; `publish` was skipped |
| 14:06:55 | a [diagnostic run](https://github.com/yeongseon/azure-functions-scaffold-python/actions/runs/37208061846) on a side branch captures the worker error |
| 14:26:28 | tag `v0.7.3` (commit `f2c0620`, which includes the fix `84ad182`) created; Release published |
| 14:31:50 | `0.7.3` uploaded to PyPI |

**Facts.** *Build & verify version* and *Library tests* succeeded; the *Azure release
certification* job failed at *Run e2e HTTP tests*. Its log shows the deployed app answering
`404` on all five probes of `/api/health`, then `Warmup failed: /api/health did not respond within
300 s`. The cause is in #365 and the diagnostic run it cites: a project generated by `0.7.2`
imports and reports five functions, but the Functions Python worker fails to index them
(`NameError: name 'func' is not defined`, `0 functions found (Worker)`), because the HTTP
templates wrapped handlers with `@with_context(strict=True)`, whose copied string annotations are
resolved in the wrapper's globals. `v0.7.3` carries the fix (#366); `v0.7.2` is an ancestor of it.
Neither failure was a deliberate decision not to publish.

**Decision:** the tag and the Release are kept unchanged as an audit record, with the existing
notice that points to `0.7.3`.

---

## v0.5.1: tag without a version bump, never published

**Facts**

- `v0.5.1` is a lightweight tag on commit `fdec8e5`, the merge of a Dependabot pull request
  committed 2026-04-17 14:07 UTC. The commit is on `main`, 17 commits after `v0.5.0`, but it
  still declares `__version__ = "0.5.0"`.
- The tag and a GitHub Release appeared at 2026-04-18 13:29:21 UTC and started two
  workflows:
  [`Publish to PyPI` run 24605726745](https://github.com/yeongseon/azure-functions-scaffold-python/actions/runs/24605726745)
  and
  [`e2e-azure` run 24605726743](https://github.com/yeongseon/azure-functions-scaffold-python/actions/runs/24605726743)
  both failed. The publish run lasted 12 seconds. The workflow at the tag checks that the tag
  equals `__version__` before building, which this commit cannot pass, but the job log has expired
  so the failing step cannot be re-read.
- PyPI has no `0.5.1`. `0.6.0` (published 2026-04-30) is the next release on PyPI, and `v0.5.1` is
  an ancestor of `v0.6.0`, so every change in `v0.5.1` shipped in `0.6.0`.

**Decision:** the tag and the Release are kept unchanged as an audit record. The Release body now
opens with a notice that `0.5.1` was not published and points to `0.6.0`; the notice is a
protected statement in `.github/release-notes.json`.

---

## v0.1.0, v0.3.0 and v0.3.1: failed publishes, tag only

These tags have neither a PyPI distribution nor a GitHub Release. A Release page would imply a
package that does not exist, so none is created.

- `v0.1.0` (annotated tag, commit `0cff7be`, 2026-03-07 01:17 UTC). Its
  [`Publish` run 22788763804](https://github.com/yeongseon/azure-functions-scaffold-python/actions/runs/22788763804)
  built the distributions, then the `publish-to-pypi` job failed; the whole run lasted 31 seconds.
  The job log has expired.
- `v0.3.0` and `v0.3.1` (annotated tags) were pushed within the same second on 2026-03-14 13:22
  UTC and point to the **same commit**, `cb9eae5` ("build: bump version to 0.3.1"), which declares
  `0.3.1`. `v0.3.0` is therefore a mislabelled duplicate, and `CHANGELOG.md` has no `0.3.0`
  section. The `Publish to PyPI` runs for
  [`v0.3.1`](https://github.com/yeongseon/azure-functions-scaffold-python/actions/runs/23088794710)
  and [`v0.3.0`](https://github.com/yeongseon/azure-functions-scaffold-python/actions/runs/23088794773)
  both failed within seven seconds. The job logs have expired, but the next commit that touched the
  workflow, `623f625`, 81 minutes later, was titled "correct pypi-publish action ref and unify
  environment to production": at the tags the workflow pinned
  `pypa/gh-action-pypi-publish@ed0c539d650490cc3f3bc7e81ddedff400bb7cf5 # v1.13.0`, and that SHA is
  not a commit of that repository (the GitHub API answers *No commit found*). That fits runs that
  fail within seconds, but it is the likely cause, not a confirmed one.
- The first version on PyPI is `0.3.2` (2026-03-21). All three tags are ancestors of `v0.3.2`, so
  their changes shipped in it.

**Decision:** keep the three tags unchanged and unreleased. `v0.3.0` must never be used as a
release: it carries the content of `0.3.1`, which was not published either.

---

## GitHub Releases added for published versions

These versions were already on PyPI and already had a tag, but no GitHub Release. The Release was
added afterwards on the **existing** tag; no tag, package file or date was changed. Notes are
reconstructed from `CHANGELOG.md` and cross-checked against the commits between the tags: `0.4.0`
lists 29 items for 29 non-merge commits (plus 8 merge commits) and `0.5.0` lists 2 items for 2
commits. Their authors are the repository owner and Dependabot, so no contributor is credited.

| Version | PyPI upload (UTC) | Tagged commit | PyPI attestation |
|---|---|---|---|
| `0.4.0` | 2026-04-08 | `b33da92` | built from the tag at this commit |
| `0.5.0` | 2026-04-09 | `1b8a06e` | built from the tag at this commit |

Publishing was not yet gated on the Azure certification when these two were released (the gate
was added on 2026-08-13 in #222), and the separate `e2e-azure` runs on both tags failed, so
these two releases should not be read as having passed that certification.

GitHub orders Releases by the date of their tag, so each added Release appears next to its
neighbours rather than at the top of the list; the time it was added is recorded as its
publication time. Older Release bodies link to the former repository name
`azure-functions-scaffold`; GitHub redirects those URLs, including compare links, to the current
repository.

---

## Checking the history automatically

`make release-audit` re-reads Git tags, GitHub Releases, `CHANGELOG.md` and PyPI and exits
non-zero for any discrepancy that is not an approved exception. It only reads: it never moves,
creates or deletes a tag, a Release or a package. Set `GH_TOKEN` to stay under GitHub's anonymous
rate limit, for example `GH_TOKEN=$(gh auth token) make release-audit`.

| Code | Meaning |
|---|---|
| `TAG_VERSION_MISMATCH` | the tagged source declares a different version than the tag |
| `TAG_NOT_ON_MAINLINE` | the tagged commit is not on the history of `main` |
| `TAG_ONLY` | a tag with neither a PyPI distribution nor a GitHub Release |
| `PYPI_WITHOUT_TAG` | published to PyPI, but no Git tag exists |
| `PYPI_WITHOUT_RELEASE` | published and tagged, but no GitHub Release exists |
| `RELEASE_WITHOUT_PYPI` | a GitHub Release exists, but nothing was published to PyPI |
| `RELEASE_WITHOUT_TAG` | a GitHub Release exists, but its tag does not |
| `CHANGELOG_MISSING` | tagged, released or published, but `CHANGELOG.md` has no section for it |

The approved exceptions are the cases documented on this page, kept in
`.github/release-audit.json` with their reason and a link to the section that explains them. An
exception must match the findings exactly, so one that no longer applies, or no longer covers
everything found for that version, fails the audit instead of going stale. A release younger than
12 hours that is still in the publish gate is reported as pending rather than as a failure. Do not
edit the file to silence a real defect: fix forward, or record the case here with its evidence.

Two narrower commands are meant for the release pipeline. `python -m tools.release_audit
check-tag vX.Y.Z` checks that the tagged source declares that version, that the commit is on
`main` and that `CHANGELOG.md` has its section. `check-published vX.Y.Z --wait-minutes N` waits
until PyPI serves the version. Exit codes are 0 for clean, 1 for a discrepancy and 2 when the
audit itself could not run.

---

## How this was verified

1. **Tag, commit and version.** `git show vX.Y.Z:src/azure_functions_scaffold/__init__.py` gives
   the declared `__version__`, and `git merge-base --is-ancestor vX.Y.Z origin/main` tells whether
   the tag is on the history of `main`.
2. **PyPI.** The [JSON API](https://pypi.org/pypi/azure-functions-scaffold/json) lists each
   version's files, upload time and yanked state.
3. **PyPI files against the tagged commit.** The snippet below compares the package files in the
   sdist with the package directory at the tag, using Git blob IDs. All 15 published versions are
   identical to their tags. Run it from a clone that has the tags.
4. **PyPI attestations.** `https://pypi.org/integrity/azure-functions-scaffold/<version>/<sdist file>/provenance`
   returns an attestation whose certificate records the source commit and the workflow run. For
   all 15 published versions the attested commit equals the tagged commit.
5. **Workflow runs.** The Actions API keeps run metadata, and job logs for about 90 days. The logs
   of the `v0.7.2` and `v0.9.0` runs and of the diagnostic run cited in #365 were read; those of
   the older runs have expired.

```python
import hashlib
import io
import json
import subprocess
import tarfile
import urllib.request

version, tag = "0.4.0", "v0.4.0"
meta = json.load(
    urllib.request.urlopen(f"https://pypi.org/pypi/azure-functions-scaffold/{version}/json")
)
sdist = next(u["url"] for u in meta["urls"] if u["packagetype"] == "sdist")


def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


shipped = {}
with tarfile.open(fileobj=io.BytesIO(urllib.request.urlopen(sdist).read())) as tar:
    for member in tar.getmembers():
        _, found, name = member.name.partition("/azure_functions_scaffold/")
        if member.isfile() and found and "__pycache__" not in name:
            shipped[name] = blob_id(tar.extractfile(member).read())

listing = subprocess.run(
    ["git", "ls-tree", "-r", f"{tag}:src/azure_functions_scaffold"],
    capture_output=True,
    text=True,
    check=True,
).stdout
tagged = {line.split("\t")[1]: line.split()[2] for line in listing.splitlines()}
print(
    "identical"
    if shipped == tagged
    else sorted(k for k in shipped.keys() | tagged.keys() if shipped.get(k) != tagged.get(k))
)
```

---

## Rules for the future

- Never move or delete a tag, and never re-upload or replace a published file to repair history.
  Record the case here instead.
- Do not create a tag for a commit that did not produce the published package.
- When a GitHub Release is added for an existing tag, say so in its notes. Mark a release that was
  never published as such.
- Use PyPI, not a GitHub Release, to decide whether a version was published.
