# ADR 0004: preserve late RNA sources by review revision

Status: Accepted for the requested post-QC workflow, 2026-11-07.

## Context

Post-QC fusion/splice workbooks arrive after the initial run import. Rewriting
`ReportRecord.report_data` would change the source facts beneath older saved or
final reviews. Reimporting the complete run would duplicate work and conflict
with existing source fingerprints and report identity.

## Decision

Keep the original report immutable. Append `ReportSourceRevision` records with
an effective review revision, validated full source document, actor/time and
private raw workbook archive. Resolve every current/historical source/review
pair using its revision. Reopening history binds its original sources to the
new draft; export deduplication compares source identity as well as review JSON.

Use a two-step selected-file upload. A
[Django signed value](https://docs.djangoproject.com/en/5.2/topics/signing/)
binds the preview to hashes, actor, exact RNA linkage, source identity and draft
revision/version. Application rechecks that identity inside a
[database transaction](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).
No files are staged persistently before confirmation.

The replacement unit is an exact RNA sample/event category present in a nonempty
workbook. Replaced candidates start unreviewed; other findings and notes remain.
Technical QC is explicit source evidence, separate from v5 human clinical class.
Known reversed columns are disclosed; colors never authorize inclusion.

## Consequences and alternatives

- Older reports/reviews remain readable; migration 0015 is additive.
- Database backup size grows with raw workbook archives, bounded per report.
- Historical source copies consume more JSON space than a delta model, but avoid
  reconstructing clinical facts through a chain of potentially broken patches.
- Empty-file withdrawal is intentionally unsupported. A future explicit removal
  command needs its own confirmed scope and audit semantics.
- The new adapter, source resolver and upload module own this workflow; no
  special network-directory traversal is added to the general discovery scanner.
