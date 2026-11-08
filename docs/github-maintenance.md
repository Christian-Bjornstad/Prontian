# GitHub and dependency maintenance

## Before merging

All changes use a short-lived pull request against `main`. Four required GitHub
Actions checks run: **quality**, **tests (ubuntu-latest)**,
**tests (windows-latest)** and **browser**. The same protection applies to the
repository administrator. A single-maintainer project does not require another
person's approval, but the tests must pass and conversations must be resolved.
Force pushes and deletion of `main` are disabled. Merged branches are deleted
automatically; old CI evidence stays available in Actions history.

The quality job checks manifests, lint, formatting, documentation, diagrams,
dependency audits and migration consistency. Tests exercise the complete core
suite on Linux and Windows, plus Django persistence/authorization. Browser tests
install the Chromium revision supplied by the pinned Playwright version.
Jobs have explicit time limits and a read-only repository token.

## Dependency changes

1. Update a direct requirement or review a grouped Dependabot proposal.
2. Regenerate `requirements-lock.txt` from `requirements-desktop.txt` with `uv`.
3. Regenerate `requirements-dev-lock.txt` constrained by the runtime lock, using
   the [contributing commands](../CONTRIBUTING.md#dependency-files).
4. Run `python scripts/check_dependencies.py` before installation. The gate uses
   only the standard library and requires one exact universal version per package.
5. Install the locks, run `pip check`, run the affected workflows and both audits.
   Use `npm ci --ignore-scripts` to prove the Node lock is reproducible.
6. Wait for all four checks on the latest PR commit, merge, and verify `main` CI.

Dependabot groups Python, JavaScript tooling and Actions separately to reduce
competing PRs. The Python maintenance group accepts minor/patch updates. Django
5.2 and PyQt6 6.11 remain on their validated feature series; routine updates to
those packages are patch releases. A framework/GUI series upgrade needs a separate
migration and validation change. Routine major `pyee` and minor/major Qt-runtime
updates are left to their parent packages' compatibility constraints. Security
reports and CI audits remain active. Configuration follows the
[GitHub Dependabot options](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference).

The input/lock gate detects manifest drift and shared runtime/dev mismatches;
it does not claim to replace the resolver's full transitive dependency checks.
`pip install` and `pip check` verify the actual installed graph. Do not edit
generated lock entries independently just to silence a failing dependency test.

## Recovery example: 8 November 2026

Several individually merged dependency proposals left `main` un-installable:
Playwright 1.64.1 requires `pyee >=13,<15`, while the development lock requested
16.0.1. PyQt6 6.11 requires its compatible Qt runtime, but its lock was raised
to 6.12.0. Node's lock used jsdom 31.0.0 while the manifest still requested 30.1.3.

Regenerating the universal locks selected pyee 14.0.0 and Qt 6.11.2, while keeping
the intended Playwright 1.64.1 and ReportLab 5.1.0 updates. Synchronizing the Node
manifest retained jsdom 31.0.0 and Mermaid 12.3.0. Clean installs and actual test
execution verify these combinations; no tests or audits are disabled to make an
upgrade appear green. The new regression checks cover these input/lock failures.

The first grouped proposal after recovery also attempted Django 6.1 and PyQt6
6.12, while retaining Qt 6.11. Installation rejected that combination. Its small
maintenance changes were separated: Ruff 0.17.4, coverage 7.17.2, filelock 4.2.9,
platformdirs 4.14.5 and sqlparse 0.6.1. The Django/Qt series upgrade was deferred
explicitly, and their routine update rules now preserve the validated series.

## Local tools

Use Python 3.14 and a current Node.js 24 release, at least 24.15.0 for jsdom 31.
CI selects the latest available Node 24 runtime. Node packages are developer
tools; the clinical desktop application does not depend on Node.js.

## Public collaboration

Issue forms request synthetic reproductions and environment details. The PR
template asks for behavior, validation and dependency regeneration evidence.
Sensitive reports go through [private vulnerability reporting](https://github.com/Christian-Bjornstad/Prontian/security/advisories/new).
Screenshots, local logs and production exports are reviewed before public sharing.
The repository's documentation lives in `docs/`; the About link points to the
maintained user guide.
