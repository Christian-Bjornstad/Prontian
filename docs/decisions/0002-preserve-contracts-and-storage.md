# ADR 0002: preserve persisted identities during rebranding

Status: accepted, 2026-11-01.

The public product and launchers use Prontian. Existing Python package names,
JSON schema identifiers, Django app/table names, migration history, environment
variables, secret key and database locations remain compatible.

Renaming every internal identifier would introduce schema/data migrations and
could strand an existing installation. Those changes offer no report behavior
benefit. Document compatibility names explicitly instead. A future migration
must have a separately tested upgrade/recovery plan; never silently create an
empty replacement database after failing to locate the intended one.
