# Post-QC RNA and MOL CNV appendices

Requested 7 November 2026. This specification records the supplied wishlist and
the confirmed requirement to support both standard and reversed QC columns.

| Capability | Responsibility | Depends on |
| --- | --- | --- |
| post-qc-rna | Select late XLSX files, preview identity/QC, preserve source versions | Existing report access and review concurrency |
| rna-reporting | Exon nomenclature and independent clinical classification | post-qc-rna |
| cnv-appendices | Include A2 then B3/C1 in landscape MOL PDF | Existing immutable plot assets |

## Acceptance criteria

- A reviewer can select one or more fusion/splice candidate workbooks from the
  report, including a day after the initial run import, without rescanning a run.
- Preview shows source filename, exact RNA sample, genes/exons, percentage,
  consequence, QC and any reversed-column interpretation. Application requires
  confirmation of the same bytes and the current draft version.
- DNA/RNA linkage is exact and comes from imported source evidence. Similar ID
  prefixes and a manual file selection cannot establish linkage.
- Raw workbook bytes and every older report/review source snapshot are preserved.
  Late data never silently changes an exported or finalized historical revision.
- QC PASS/OK means technically eligible only. Human INCLUDE/EXCLUDE and clinical
  classification (including ONCOGENIC and VUS) are separate saved choices.
- Display example: `AKT3 (exon 1)::CEP112 (exon 17), 13% read support,
  out-of-frame`. Raw support 12.676 remains available in the source table.
- Both `Outcome=out-of-frame, QC_Verdict=PASS` and
  `Outcome=OK, QC_Verdict=out of frame` are supported and disclosed in preview.
- Landscape MOL PDFs append A2 alone, followed by B3 and C1 together, using
  source pages 2, 4 and 5 of the standard nine-page CNV overview. Portrait ESMO
  output is unchanged. Missing/unsupported plots are explicitly identified.
- Synthetic regression tests cover source identity, QC mapping, stale writes,
  authorization, historical exports and actual PDF image placement. No attached
  workbook, presentation or patient material is committed to the public repo.

## Implementation and verification

Use existing Python 3.14, Django 5.2, openpyxl, ReportLab, PDFium and vanilla JS.
Do not add dependencies. Source adapters live in `pronto_report/adapters`,
HTTP/persistence in `pronto_web/reports`, PDF layout in `renderers`, and tests
beside the existing suites. New boundary functions explain invariants in
docstrings. Keep parser bounds, CSP, attribution and compare-and-swap checks.

Run focused pytest tests while implementing, then the commands in
[CONTRIBUTING](../CONTRIBUTING.md): quality/lint/format/documentation checks,
core tests, Django request tests, migration checks and real Chromium workflows.
