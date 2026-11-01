# Changelog

## Unreleased — independent Prontian repository

- Establish Prontian from the current desktop application with a clean public
  source history, retaining GPL and source acknowledgements.
- Retire unused legacy PowerPoint code, configuration, Office templates, transit
  forms, historical logs, old fixtures and upstream Docker publishing workflows.
- Rename product launchers and visible report/application branding to Prontian;
  preserve existing configuration, schema and database identifiers.
- Reduce repeated discovery filesystem checks and index exact source scopes.
  The recorded 100-sample local synthetic median improves from 2.99 s to 0.55 s.
- Fix the missing Qt confirmation-dialog import for shared database selection.
- Harden the browser-only launcher against replacement keys and back up existing
  databases before pending migrations.
- Keep clinical classification available in compact variant tables and update
  detail workflows to use the explicit Full table control.
- Add Python/JavaScript lint and formatting, dependency locks/audits, complete
  source-file documentation and architecture/database/review Mermaid diagrams.
- Add Windows/Linux and browser CI, documentation checks and operations guidance.
- Update the PDF test reader to pypdf 6.21.4 after reviewing its security fixes.
- Update pytest to 9.2.0 for corrected temporary-directory handling and audit
  the complete development dependency lock in CI.

Earlier application history is available in the original PRONTO project.
The inherited application version is 0.8.0; no release tag is implied here.
