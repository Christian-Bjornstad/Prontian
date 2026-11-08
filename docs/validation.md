# Validation record

## GitHub and dependency recovery — 2026-11-08

Dependency installation failed on `main` after separately merged updates.
The resolver reproduced the incompatible pyee 16/Playwright 1.64.1 pins, and
`npm ci` reproduced the jsdom input/lock mismatch. Universal lock regeneration
also corrected the Qt runtime to PyQt6's supported 6.11 series.

| Check | Result after repair |
| --- | --- |
| Python/core suite with resolved upgrades | 588 passed; 18 existing platform/capability skips |
| Django request/persistence suite | 133 run, OK, one existing platform skip |
| Chromium workflows | 82 passed with Playwright 1.64.1 and matching Chromium 156 |
| Dependency contract regression suite | Five passed |
| Clean dependency installation | Locked Python environment, `pip check` and `npm ci` passed |
| Runtime/development Python audits | No known vulnerabilities |
| Node tooling audit | Zero vulnerabilities |
| Quality/documentation | Lint, format, 267-source reference, links and ten Mermaid diagrams passed |
| Migration consistency | No changes detected |

The shared-lock mutation was caught by its regression; the checker was restored
byte-for-byte and all five contract tests passed again. A separate read-only
review found no actionable issues. Existing tests, audits and skip policy were
preserved. ReportLab 5.1.0, jsdom 31.0.0 and Mermaid 12.3.0 remained in the tested
environment; compatibility pins resolve pyee 14.0.0 and Qt 6.11.2.

The repository now requires all four checks for `main`, including administrator
merges, and requires a PR without an extra-person approval requirement. Six
branches were removed only after verifying they were already merged. Historical
failed runs remain as evidence. See [maintenance](github-maintenance.md).

## Post-QC RNA and MOL appendices — 2026-11-07

| Check | Local result |
| --- | --- |
| Full Python/core suite | 583 passed; 18 existing platform/capability skips |
| Core package coverage | 82%; separate Django/browser runs are not added to this figure |
| Django request/persistence suite | 133 run, OK, one existing platform skip |
| Full Chromium suite | 82 passed |
| Affected browser workflows after final UI polish | 11 passed |
| Late-source HTTP/history/QC regression suite | 14 passed |
| PDF/presentation/appendix checks | 10 passed |
| Discovery metadata-budget regressions | Five passed |
| Owned code and generated reference | 265 source files documented |
| Lint, formatting, links and Mermaid | Passed; ten diagrams parsed |
| Migration consistency and installed requirements | No model changes pending; pip check passed |
| Complete Python development dependency audit | No known vulnerabilities found |
| Node dependency audit | Zero vulnerabilities |

The synthetic tests cover standard/reversed QC columns; exact filename/row/RNA
linkage; duplicate or mixed samples; stable event identity; late source preview
without writes; changed-byte, stale-version and cross-user rejection; independent
RNA class persistence; PASS-only inclusion on save/finalize/export; unchanged old
source documents; source restoration on REOPEN; legacy sample-header aliases;
missing private archives; and a source commit interleaved with report rendering.
Export-freeze coverage proves equal review choices cannot deduplicate unequal
source facts. Input and screenshot fixtures contain generated demonstration data.

An inverted post-QC PASS guard was caught by the new failure regression. The
source file was restored byte-for-byte and the regression passed again. No
checks or existing behavior assertions were disabled. Existing PDF test setups
now persist their declared CNV overview bytes, matching a real imported report.

PDF checks inspect actual images and colors: source page 2 alone, then pages 4
and 5 together. Synthetic output was also rasterized for visual QA, including
the partner/exon text, independent clinical class and both CNV appendix pages.
The received wishlist workbook/PPTX remain outside the public repository.

See [workflow and limits](post-qc-rna.md), [specification](spec-post-qc-rna.md),
[source-version decision](decisions/0004-version-late-rna-sources.md), and
[performance proposals](performance.md#faster-late-file-access-and-next-improvements).

## Original repository transition — 2026-11-01

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
| Complete Python development dependency audit | No known vulnerabilities found after security updates |
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
- Linux browser checks normalize PDF font ligatures before comparing every
  required heading, and wait for the native dialog close event before asserting
  that table zoom was restored. These preserve the original behavior assertions.

See [performance](performance.md) for baseline/intermediate/final measurements.

The PDF inspection test dependency was updated from pypdf 6.16.2 to 6.21.4 after
the repository security scan identified parser denial-of-service advisories.
The seven focused PDF/presentation tests passed with the patched version.
See the [upstream security release](https://github.com/py-pdf/pypdf/releases/tag/6.21.4).

Pytest was updated to 9.2.0 after reviewing the temporary-directory advisory
[GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g) and the
[upstream release notes](https://github.com/pytest-dev/pytest/releases/tag/9.2.0).
CI audits the complete development lock, including the runtime dependency graph.

See [contributing](../CONTRIBUTING.md) for repeatable verification commands.
The public CI badge links to Windows/Linux, browser and quality results for each
published commit. Site-specific SMB/Citrix performance and restore/clinical
acceptance remain in [production readiness](production-readiness.md).
