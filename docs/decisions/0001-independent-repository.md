# ADR 0001: independent application repository

Status: accepted, 2026-11-01, implementing the owner's explicit request.

Prontian starts from desktop commit `b1a41f1` as a standalone repository with a
fresh public Git history. Only tracked source and intentional public fixtures
are copied. Private environments, databases, credentials and generated output
are excluded. The original checkout remains a recovery/reference source.

The old PowerPoint command is not used by the desktop/report application. Its
templates, transit forms, legacy config, logs, tests and publishing workflow are
removed together. Retain runtime adapters that read existing PRONTO/TSOPPI
outputs: they are input compatibility code, not redundant legacy applications.
Preserve GPL, original source acknowledgements and third-party licenses.
