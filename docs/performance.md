# Folder discovery performance

Measured 2026-11-01 on the same Windows workstation with CPython 3.14.0.
The disposable benchmark creates synthetic raw/reviewed folders outside the
repository, never reads patient data and deletes its own fixture on completion.

```powershell
.\.venv\Scripts\python.exe scripts\benchmark_discovery.py --samples 100 --repeat 3
```

## Results

100 samples, 602 files, three scans per implementation:

| Implementation | Scan 1 | Scan 2 | Scan 3 | Median | Path.lstat | Path.stat | Opens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Source baseline `b1a41f1` | 5.7865 s | 2.9029 s | 2.9915 s | 2.9915 s | 13,252 | 2,810 | 1,404 |
| Per-scan ancestor/linkage caches | 2.8986 s | 1.8328 s | 1.6714 s | 1.8328 s | 1,429 | 2,310 | 1,104 |
| Plus exact source-scope index | 1.9335 s | 0.5404 s | 0.5543 s | 0.5543 s | 1,429 | 2,310 | 1,104 |

The measured median improves by about 81.5% (5.4×). Path.lstat calls fall 89.2%;
file opens fall 21.4%. These counters count Python Path operations, not physical
SMB requests. Path.stat can include internals called by Path.lstat. The same
counter instrumentation is used for all variants. Scan 1 includes more cold
initialization than later scans; do not compare one cold value to one warm value.

## What changed and why

Each source file previously rechecked every ancestor during discovery, table
reading and linkage reading. Discovery now reuses successful ancestor checks
only for that scan. Every leaf is still checked, and later import performs an
independent full-path check. Sample lists and linkage comments also reuse
bounded scan-local content instead of reopening identical files.

Source matching previously traversed all candidates for each sample and source
role, repeatedly locating run boundaries. A per-scan index now groups candidates
by role, exact run, version and sample directory. Existing scope/identity
predicates still run over those candidates. No persistent patient-data cache
or new database table was added.

## Regression protection and limits

`test_discovery_performance.py` enforces a deterministic metadata-call budget
and checks exact reviewed source selection, fresh scans after source changes,
Windows root reparse rejection and independent ancestor revalidation after a
scan. Existing version/linkage/import tests cover changed-source rejection,
ambiguous files, cancellation and transactional failures.

This measures **discovery**, not full import, plot rasterization, report loading
or PDF export. There is no measured SMB/Citrix speed claim. Before operational
rollout run the same sample-count measurement on the intended filesystem with
approved test material. Record cold/warm runs separately and verify that report
counts and chosen sources match. Choosing the nearest run root or exact date
also avoids scanning unrelated historical runs.

## Faster late-file access and next improvements

The [post-QC upload flow](post-qc-rna.md) reads only the chosen workbooks. It does
not rediscover a run, reopen all its variant tables or traverse historical roots.
New imports persist their already validated RNA IDs, avoiding a second linkage
lookup for a later upload. No SMB timing claim is inferred from this design.

Recommended next steps, in priority order:

1. **Operational convention:** use one known transfer root and exact run ID/date.
   Put post-QC outputs in predictable `fusions`/`splice` directories and keep the
   exact RNA ID in each filename. This improves lookup without code changes.
2. **Remember the last post-QC folder per workstation:** a native file picker can
   restore a saved approved location. Browser file inputs cannot be assigned an
   arbitrary network starting directory by the application; do not promise that
   a web-only picker can control the operating system's folder history.
3. **Producer-generated run manifest:** a small versioned JSON/TSV list containing
   exact sample, role, relative path, size and checksum would avoid recursively
   searching a run. Validate containment, identity and current bytes again at
   import; a manifest must not authorize a path by itself.
4. **Measure the actual bottleneck on the intended share:** record directory
   enumeration, table reads, XLSX parsing, plot rendering and database time
   separately, with cold/warm measurements. Optimize the slow stage before adding
   network parallelism or a persistent patient-data cache.
5. **Optional explicit refresh of known post-QC paths:** remember exact confirmed
   paths with permission-appropriate storage, then check only those files when
   the reviewer requests refresh. Always show changed SHA-256/QC and preview;
   never silently replace a clinical source because a filesystem watcher fires.

These are proposals. The current change implements direct workbook selection and
persisted validated linkage, and retains the existing bounded run-discovery cache.
