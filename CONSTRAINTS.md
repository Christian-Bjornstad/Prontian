# Maintained quality contract

The commands in CONTRIBUTING.md and CI enforce the same baseline.

- Python 3.14. Ruff checks all owned Python files for syntax, undefined names,
  unused code/imports and import ordering; Ruff format checks all owned Python.
- Every behavior change preserves existing tests and adds a meaningful
  regression when needed. Removing a retired feature's tests must accompany
  removal of that feature and an explanation. Never skip tests to hide failures.
- Import discovery remains bounded (1–5 roots, 50,000 files, depth 30,
  25 MiB per table and 10,000 rows); no fuzzy sample identity or link traversal.
- The synthetic discovery test permits at most eight Path.lstat calls per
  source file. Record wall-clock results separately; local timings are not an
  SMB latency guarantee. Caches are scoped to one discovery call.
- New source files need a module docstring and an entry in the generated code
  reference. Public boundary functions document purpose and invariants.
- Documentation links, JavaScript syntax and owned browser lint must pass.
- Runtime and development dependency audits must pass without ignored advisories.
- No production data, credentials, SQLite files, raw reads or local configuration
  may be committed. Public fixtures have explicit provenance.
- Preserve schema versions, migrations, immutable source values, optimistic
  concurrency and report authorization. No production key or DB replacement to
  recover an access error.

This contract records the requested repository baseline. Coverage is reported
as evidence rather than a fabricated percentage target. Site-specific clinical
validation and deployment limits are recorded in docs/production-readiness.md.
