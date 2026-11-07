# Changelog

## Unreleased — post-QC RNA and MOL CNV appendices

- Select late fusion/splice XLSX files directly from RNA review, preview exact
  sample linkage, technical QC and standard/reversed QC column interpretation,
  then confirm the same files against the current draft.
- Preserve raw workbooks and versioned source snapshots without changing
  earlier saved/final reports. Reopening an old review retains its source version.
- Add ReviewState 5.0 for independent RNA clinical classes such as ONCOGENIC
  and VUS. Replaced source categories require fresh review; FAIL/unreviewed
  post-QC events cannot be included, finalized or exported as included findings.
- Format source-declared partner/exon nomenclature and rounded report support,
  while preserving exact original percentages and all source annotations.
- Append A2 on one page, then B3/C1 together, to landscape MOL PDFs. Missing or
  unfamiliar CNV overview layouts are disclosed instead of mislabeled.
- Add migration 0015. Desktop startup backs up an existing database before
  applying it; retain the original installation key and all private source data.

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
