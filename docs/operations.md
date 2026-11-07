# Operations and recovery

The supported launch path is the local desktop app. Its WSGI listener is bound
to loopback. Keep source code and private operational data separate. The
repository contains no deployed database, credentials or installation key.

Migration 0015 adds late source versions. Existing desktops back up the database
before migrating. Retain original keys, database and `raw_imports` together.
Raw post-QC workbooks are also stored inside the private database source-version
archive, so database backups now include them. Never roll back the schema by
dropping source-version tables; restore the complete pre-upgrade backup instead.

Desktop runtime sets `PRONTO_RAW_IMPORT_ROOT` to its private `raw_imports` root.
When using a separately configured local web launcher, set that value explicitly
if older reports need archived DNA/RNA linkage for late post-QC imports. Newly
imported reports retain validated RNA IDs in SQL. The path is not a public upload
directory. See [post-QC workflow](post-qc-rna.md).

## Installation and identity

Install 64-bit Python 3.14 and the desktop requirements. Use a virtual environment
or the existing Python FELLES launchers. The Qt first-account flow creates an
installation administrator; create personal reviewer accounts afterward. An
administrator role inside Prontian does not grant filesystem or SMB access.

The product is Prontian. Compatibility identifiers remain unchanged:

| Identifier | Purpose |
| --- | --- |
| `pronto_desktop`, `pronto_ingest`, `pronto_report`, `pronto_web` | Python imports |
| `reports_*` tables and migrations | Existing database schema |
| `%LOCALAPPDATA%\PRONTO\desktop.json` | Per-user desktop settings |
| `pronto-installation.json` | Optional shared installation locator |
| `.local-web`, `.local-web2` | Recognized existing managed data locations |
| `pronto.sqlite3`, `database/pronto.sqlite3` | Recognized database layouts |
| `PRONTO_*` environment variables | Existing configuration API |

Do not rename these files to match the product. An explicit existing database
can be selected without copying it:

```powershell
.\.venv\Scripts\python.exe -m pronto_desktop --data-root 'C:\private-data' --database 'C:\private-data\database\pronto.sqlite3'
```

Replace example paths with the installation's actual paths. Keep the original
`secret.key` in its data root. A new repository is not an empty database upgrade.

## Upgrade

1. Identify the current code revision, Python version, data root and active DB.
2. Stop all app/server processes using that database. Preserve the current code
   and environment so the previous installation can be restarted if needed.
3. Create a complete backup as described below. Restore it to a separate test
   location and verify report counts, one finalized revision and a working draft.
4. Install the new code and pinned dependencies. Start against the intended data
   root. The desktop takes a SQLite backup before pending schema migrations.
5. Verify login, report grants, source assets, save/conflict behavior and PDF
   export with an approved test case. Confirm the active database path.
6. Record the installed commit and validation result. Retain the previous backup
   until the agreed recovery period expires.

`python -m pronto_desktop --check` initializes configuration and applies pending
migrations without opening the main window. It is not a read-only diagnostic;
use it on an isolated copy first when evaluating an upgrade.

## Complete backup

Use the app's **Sikkerhetskopi** action for an online SQLite backup. It uses
SQLite's backup API and checks integrity, including committed WAL content.
The automatic pre-migration backup is useful but does not replace retention
and off-machine backup ownership.

For a consistent complete backup, stop writers and retain:

- the SQLite backup and exact source-code revision/dependency versions;
- original `secret.key`, per-user configuration and shared locator as needed;
- `raw_imports`, local biomarker list and any presentation/source side files;
- private saved alignment store and staging policy/configuration;
- local reference FASTA/FAI pairs and their build/version provenance.

Report assets and presentation figures stored in SQL are included in a SQL
backup; raw source archives and alignment bytes outside SQL are not. Encrypt
and restrict backups according to the installation's approved storage policy.
Choose and record a backup owner, frequency, retention, recovery point and
recovery time target before operational use.

## Restore and rollback

Restore into a separate private directory. Preserve the installation key;
never create a replacement key to bypass a startup error. Inspect SQLite with
`PRAGMA integrity_check`, start the matching code against that copy, and verify
reports, revision history, working draft, assets and granted/denied accounts.
Only then update the installation's explicit database location.

Do not point older code at a database migrated by newer code. Roll back code,
environment and the matching complete backup together. Preserve any newer work
separately for investigation rather than overwriting it.

## Access errors and shared installations

Missing database, missing key and access denied are distinct startup failures.
Selecting a different file is appropriate for a stale location; it does not
repair denied filesystem permissions. Existing installations never silently
receive an empty replacement database or key.

`PRONTIAN_REPARER_TILGANG.cmd` is an explicit repair action. The PowerShell tool
backs up ACL descriptors and only repairs eligible protected ACLs owned by the
current user within managed roots. Customized or foreign-owned ACLs are skipped.
Review with `scripts/repair_shared_access.ps1` without `-Apply` first. Site
administrators must resolve share-level or institutional access policies.

A shared program folder and a shared locator are supported compatibility paths.
They do not certify SQLite on SMB for concurrent multiuser writes. Use a single
active workstation writer until a server/database deployment is separately
designed and load-tested.

## Diagnostics

| Symptom | Check |
| --- | --- |
| App cannot find the DB | Actual active data root; saved per-user location; shared locator |
| Existing key is missing | Restore the original key or select its correct data root |
| Access denied | Filesystem ACLs on DB, journal directory, source archive, backup and key |
| Port occupied | Stop the owning app or select another local port; identity check prevents blind reuse |
| PDF source plots fail | Installed `pypdfium2`; PDF decoder/page bounds; optional Poppler fallback |
| No run found | Exact date/ID; nearest parent; lookup searches at most three directory levels |
| Source conflicts | Exact run/sample/version and explicit DNA/RNA linkage; inspect preview |
| Save returns 409 | Keep local edits and reload the current working version |
| IGV cannot display a region | Reference build, FASTA/FAI pair, alignment index and interval coverage |

Bootstrap logs normally live in `%LOCALAPPDATA%\PRONTO\logs\bootstrap.log`,
with `%TEMP%\PRONTO\logs` as a fallback. Error messages show the actual location.
Logs can include private paths; keep them in approved internal storage and
redact before reporting a software issue.

## Environment and optional alignment controls

Core web settings are `PRONTO_DJANGO_SECRET_KEY`, `PRONTO_DJANGO_DB` and
`PRONTO_STATIC_ROOT`. DesktopRuntime provides the key/database for local
startup. `PRONTO_WORKING_DRAFTS` enables the current persistence mode; the local
settings enable it explicitly. Tests use a separate synthetic settings module.

Alignment policy, quotas, staging, source roots and reference variables are
documented in [IGV operations](igv-alignment-operations.md). Saving is disabled
until all required controls are configured. Cleanup and reconciliation commands
must operate on that installation's private store, never a public static folder.
