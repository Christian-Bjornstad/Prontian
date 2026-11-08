# Contributing to Prontian

Start with the [architecture](docs/architecture.md), [code guide](docs/code-guide.md)
and [quality contract](CONSTRAINTS.md). Keep changes small enough to review and
preserve existing source/review separation, authorization and concurrency rules.

## Development environment

Use CPython 3.14 and Node.js 24.15 or newer in the 24 series (required by jsdom 31).
Commands below use PowerShell; on Linux replace
`.venv\Scripts\python.exe` with `.venv/bin/python`.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev-lock.txt
npm ci --ignore-scripts
.\.venv\Scripts\python.exe -m playwright install chromium
```

On headless Linux, Qt tests require `QT_QPA_PLATFORM=offscreen` and the EGL/OpenGL
runtime libraries. `python -m playwright install --with-deps chromium` installs
the Linux browser dependencies. CI contains the exact installation commands.

## Fast feedback and full verification

```powershell
# Focused behavior changes
.\.venv\Scripts\python.exe -m pytest pronto/tests/ingest -q

# All deterministic static/documentation gates
.\.venv\Scripts\python.exe scripts\check_quality.py

# Core contracts, import, native GUI and helper tests
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m coverage run -m pytest -q --ignore=pronto/tests/reporting/browser
.\.venv\Scripts\python.exe -m coverage report

# Django's request/persistence tests are a separate suite
.\.venv\Scripts\python.exe manage.py test pronto_web.reports --settings=pronto_web.test_settings
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=pronto_web.test_settings

# Real Chromium report workflows
$env:PRONTO_BROWSER_EXECUTABLE = (& .\.venv\Scripts\python.exe -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); print(p.chromium.executable_path); p.stop()")
.\.venv\Scripts\python.exe -m pytest pronto/tests/reporting/browser -q

# Dependency checks
.\.venv\Scripts\python.exe -m pip_audit -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip_audit -r requirements-dev-lock.txt
npm audit --audit-level=moderate
```

The test settings use a fast password hasher only inside tests. Launchers use
the production password hashers and existing password policy. Windows cannot
run the Linux-only persistent alignment tests; Linux CI runs them with pysam.
Do not add skips to hide failures in an available capability.

## Formatting and documentation

```powershell
.\.venv\Scripts\python.exe -m ruff check . --fix
.\.venv\Scripts\python.exe -m ruff format .
npm run format
.\.venv\Scripts\python.exe scripts\document_code.py
.\.venv\Scripts\python.exe scripts\check_quality.py
```

Add a module-purpose docstring for a new Python module. Explain public boundary
functions, invariants and non-obvious reasons in source; keep cross-component
workflow explanations in the code guide. The generated file reference covers
every owned Python, JS, CSS, template, schema, launcher and support script.
Update ADRs for consequential choices, not routine formatting.

## Dependency files

`requirements.txt` contains runtime readers/renderers/web dependencies;
`requirements-desktop.txt` adds Qt. Test/browser/dev inputs extend those files.
`requirements-lock.txt` pins the full cross-platform desktop dependency graph;
`requirements-dev-lock.txt` additionally pins quality/testing tools. Install the
lock file for a reproducible environment. Do not hand-edit generated locks.

With `uv` installed, regenerate after an intentional dependency change:

```powershell
uv pip compile requirements-desktop.txt --universal --python-version 3.14 --output-file requirements-lock.txt
uv pip compile requirements-dev.txt --universal --python-version 3.14 --constraint requirements-lock.txt --output-file requirements-dev-lock.txt
```

`package-lock.json` pins Node development tools. The minimatch override selects
the advisory-fixed 11.0.1 release for tooling; ESLint and Mermaid checks verify
the resolved tooling still works. Node dependencies are not shipped with the
Python application. Review each upgrade and audit the resolved dependencies.

Run `python scripts/check_dependencies.py` before installing a proposed update.
It compares all direct input pins with their locks, requires the development
environment to contain the same runtime graph, and checks Node manifest/lock
agreement. CI runs it before installation and runs `pip check` afterward.
The compiler and package installer remain responsible for transitive compatibility.

Dependabot groups related updates by ecosystem. Regenerate Python locks on its
branch before merging if the input/lock gate fails. Do not independently raise
`pyee` beyond Playwright's supported major, or the Qt runtime beyond PyQt6's
supported minor. Keep runtime and development dependencies audited without ignored
advisories. See [GitHub maintenance](docs/github-maintenance.md).

## Changing persistence

Never modify an applied Django migration or silently mutate old JSON contracts.
Add a migration/schema version and test old documents/database recovery. Keep
ReportData immutable, reviews attributed, FINAL snapshots preserved and stale
working-draft writes rejected. Test both granted and denied accounts.

## Fixtures and public changes

Read [fixture policy](docs/fixture-and-privacy-policy.md). Prefer synthetic test
inputs generated in temporary directories. Never commit a live database,
secret/key, alignment, patient export or unrestricted log. Review binary metadata
as well as visible content. Existing migrations and licensed third-party files
are intentional retained source.

Use a short-lived feature branch. Include behavior, reason and relevant checks
in the change description. Keep formatting-only changes separate from behavior
when practical. Before pushing inspect `git diff --cached`, staged file names
and ignored local state. The changelog records user-facing effects.
