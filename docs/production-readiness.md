# Production readiness

Prontian is prepared as a maintainable local application. Passing repository
checks does not establish institutional clinical approval or validate a new
network deployment. This page identifies the remaining boundary explicitly.

## Implemented engineering controls

| Area | Current control |
| --- | --- |
| Source identity | Exact sample/run/version scope; concordant DNA/RNA claims |
| Import | Bounded readers, source hashes, changed-source rejection and per-sample SQL transaction |
| Provenance | Immutable source contract, archived inputs, review and export audit records |
| Access | Django authentication, per-report grants and independent alignment write grants |
| Requests | CSRF, command bounds, semantic validation and optimistic concurrency |
| Local host | Loopback listener, bounded threads and server identity verification |
| Startup | Persistent key, explicit existing database recovery, backup before migrations |
| Assets | Private authorized access, hash verification and decoder/page/pixel limits |
| Alignment storage | Policy gate, quotas, opaque keys, staged lifecycle and cleanup commands |
| Maintenance | Lint/format, dependency audit, Windows/Linux CI, browser tests and checked documentation |

Refer to [validation evidence](validation.md) for commands actually run and
their results. No audit trail here is described as cryptographically tamper-proof:
database administrators can alter a SQLite file outside the application.

## Required before institutional use

- Assign named clinical, technical, data and operations owners.
- Validate approved representative runs against the pipeline and current
  reporting practice, including missing sources, duplicate findings and exports.
- Confirm file permissions and data locations in the real Citrix/SMB environment.
- Run the discovery benchmark there and test interruption/cancellation and recovery.
- Define retention, disk capacity, backup frequency and recovery targets; complete
  and record a restore drill using a separate location.
- Review account lifecycle, access revocation, shared report visibility and
  institutional privacy/security requirements.
- Review report text, gene/biomarker list provenance and reference builds with
  the responsible subject-matter owner.
- Treat optional persistent alignment storage as a separate storage/retention
  decision; do not enable it merely to make local viewing work.

## Server deployment is a separate scope

The bundled workstation WSGI host and browser-only development launcher are not
a supported internet-facing deployment. A shared multiuser service needs a
production WSGI/ASGI host, HTTPS, explicit hosts/origins, secure cookies, static
asset serving, login rate limits, monitoring and an appropriate shared database.
That architecture and its concurrency/load behavior have not been established
by this repository transition. Do not expose port 8770 to a network to simulate it.

## Known maintenance work

Some rendering, validation and native UI modules remain large. Their boundaries
are documented in the code guide, and Ruff formatting makes the existing flow
readable. A wholesale rewrite would add risk without proving operational value.
Split those modules along tested responsibilities as future features require.
Coverage is reported without claiming an unmeasured target or certification.
