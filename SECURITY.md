# Security reports

Use GitHub's private vulnerability reporting for this repository when available.
Do not publish patient records, report exports, production paths, account details,
tokens or installation keys in an issue. Describe the affected commit, expected
boundary and a minimal synthetic reproduction.

Supported scope is the current maintained main branch and local workstation
launch path. See docs/production-readiness.md before designing network hosting.
Keep database backups and private stores restricted. Rotate exposed credentials
and follow the institution's incident process if operational data is involved.

Runtime dependencies are pinned and audited in CI. Browser tooling is development
only; third-party IGV remains separately licensed and versioned in its directory.
