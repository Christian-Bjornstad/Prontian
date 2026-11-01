# Validation record

Repository transition from desktop source commit `b1a41f1`, checked locally on
2026-11-01 with CPython 3.14.0, Windows and the resolved development lock file.
This record covers software verification, not institutional clinical approval.

| Check | Local result |
| --- | --- |
| Python unit/import/native/helper suite | 558 passed, 18 platform/capability skips |
| Django request/persistence suite | 119 run, OK, one platform skip |
| Focused compact/full table and review browser workflows | 25 passed |
| Full Chromium suite | 80 passed; Chromium 140.0.7339.16 |
| Python lint and formatting | Passed |
| JavaScript lint and formatting | Passed |
| Mermaid parsing | Nine diagrams passed |
| Complete code reference | 251 owned source files documented |
| Database model/migration consistency | No changes detected |
| Runtime dependency audit | No known vulnerabilities found |
| Node development dependency audit | Zero vulnerabilities |
| Clean resolved environment | `pip check` passed; retired dependencies removed |
| FELLES installer import smoke check | Passed against the clean environment |
| Synthetic example command | Generated four source folders successfully |

The core suite is `coverage run -m pytest -q
--ignore=pronto/tests/reporting/browser`. The separate Django command is
`python manage.py test pronto_web.reports --settings=pronto_web.test_settings`.
The Chromium suite uses `PRONTO_BROWSER_EXECUTABLE` set to the installed
Playwright executable and runs all of `pronto/tests/reporting/browser`.
Coverage reported 82% across configured application packages in the local core
run; it does not include the separate Django/browser runs in that figure.

Windows does not provide the pinned pysam implementation for persistent
alignment validation; Linux CI includes that dependency and exercises the
platform-specific paths. No new skips were added to make checks pass.

## Regression evidence

- Discovery metadata-budget test failed before optimization (1,960 lstat calls
  for 74 files), then passed with scan-local caching. Temporarily disabling that
  cache made the test fail again; the original implementation was restored.
- The shared database confirmation failed with NameError before the Qt import
  fix; its regression passes afterward.
- Browser-only startup tests reproduced key replacement and missing migration
  backup, then passed with the new guards using a real isolated SQLite database.
- The retired PPTX golden comparison is replaced with source→contract→HTML
  assertions for pseudonym, raw TMB/MSI values, formatted output and 30 variants.
  Tests for the retired PowerPoint program are removed with that program.
- Explicit fixture exports preserve pytest fixtures and the public bootstrap
  grant alias under lint; PBKDF2 remains available and explicit in bootstrap
  security tests while unrelated tests use a fast hasher.
- Full browser execution exposed hidden compact clinical-class controls; the
  control remains visible and technical detail workflows explicitly select Full
  table. Tests preserve duplicate identity, comments, filtering and exported state.

See [performance](performance.md) for baseline/intermediate/final measurements.
See [contributing](../CONTRIBUTING.md) for repeatable verification commands.
The public CI badge links to Windows/Linux, browser and quality results for each
published commit. Site-specific SMB/Citrix performance and restore/clinical
acceptance remain in [production readiness](production-readiness.md).
