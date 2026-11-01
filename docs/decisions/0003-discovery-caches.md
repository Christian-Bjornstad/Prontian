# ADR 0003: scope discovery caches to one scan

Status: accepted, 2026-11-01.

Measured discovery repeatedly validates the same ancestors, reparses linkage
sources and scans every candidate for each sample. Reuse successful ancestor
checks and bounded linkage/table content only within one discovery call. Index
sources by role, exact run, version and physical sample directory.

Retain existing scope and identity predicates. Each leaf is checked, a fresh
scan reads sources again, and import performs independent full-path validation,
signature checks and byte hashing. No global or persistent patient-data cache
is introduced. This reduces remote metadata work without making a preview a
durable authorization. See the regression guards and measured results in
[performance](../performance.md).
