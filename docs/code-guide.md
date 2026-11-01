# Where to change the code

The [generated code reference](code-reference.md) enumerates every owned source
file, module purpose and top-level definitions, with direct source links. It is
regenerated from source docstrings and AST declarations and checked in CI.
This guide explains how to choose the right layer before editing.

| Change | Start with | Follow through |
| --- | --- | --- |
| Native pages, dialogs, keyboard interaction | `pronto_desktop/gui.py` | `theme.py`, desktop GUI tests |
| Startup, data root, existing DB recovery | `pronto_desktop/runtime.py` | `shared_installation.py`, `storage_access.py`, runtime tests |
| Credentials and first installation account | `pronto_desktop/accounts.py` | web `user_management.py`, session/authorization tests |
| Local server lifecycle and port reuse | `pronto_desktop/server.py` | native server tests; never expose loopback handler publicly |
| Find a run by date | `pronto_ingest/run_lookup.py` | `naming.py`, run lookup tests |
| Recognize an input format or choose a version | `pronto_ingest/discovery.py` | `naming.py`, `linkage.py`, versioned discovery tests |
| Archive, fingerprint or publish an import | `pronto_ingest/importer.py` | ingest transaction, changed-source and duplicate tests |
| Read TSV/CSV/XLSX/Cancan content | `pronto_report/adapters/` | identity and adapter/import tests |
| Change report or review fields | schemas, `models.py`, `validation.py` | serialization, migration, renderers and schema tests |
| Source-derived initial review values | `pronto_report/review/source_defaults.py` | reviewed values must remain intact |
| Review inclusion, finalization or correction rules | `pronto_report/review/service.py` | command contracts, review service tests |
| Active draft save/concurrency/export freeze | `pronto_web/reports/working_drafts.py` | models, draft/request/browser tests |
| Persistent schema | `pronto_web/reports/models.py` | a new Django migration; never edit applied migrations |
| Report list/detail, authorization, alignment HTTP | `pronto_web/reports/views.py` | `urls.py`, report-grant request tests |
| HTML report structure | `renderers/html.py`, `templates/report/` | projection, report CSS/JS and browser tests |
| Small variant columns and source details | `renderers/variant_columns.py`, `source_fields.py` | `static/table-views.js`, full-table browser tests |
| Current CNV/RNA/finding sections | `renderers/review_v4.py` | `review_v3.py` for older contracts; matching JS files |
| Report and presentation PDF | `renderers/report_pdf.py`, `presentation_pdf.py` | `reports/pdf_export.py`, PDF parity/request tests |
| Summary HTML | `renderers/summary_html.py` | `html_export_audit.py`, export tests |
| PNG/PDF plot decoding | `renderers/assets.py`, `pdfium.py` | resource bounds and plot tests |
| Presentation figure upload | `reports/figures.py` | figure model, review references and export tests |
| IGV in the browser | `static/report-igv.js` | private references and alignment ranges; IGV browser tests |
| Alignment policy/quotas/private file storage | `reports/alignment_config.py`, `alignment_store.py` | registry, command lifecycle, cleanup/reconciliation tests |
| Local gene/biomarker membership | `review/gene_registry.py`, `biomarker_list.py` | static gene data and source-default tests |
| Purely synthetic demo reports | `reports/synthetic_data.py`, `synthetic_plots.py` | demo management commands and synthetic demo tests |

Paths in the table are relative to the owning package. The generated reference
resolves every concrete path. Related files belong together; a display change
must not silently change imported facts or persistence rules.

## Browser code ownership

| Owned JavaScript file | Responsibility |
| --- | --- |
| `report.js` | Tabs, editable review state, validation, save/finalize and exports |
| `working-draft.js` | Working-draft protocol integration |
| `review-v3.js` | Linked version-3 review fields, plot controls and section QC |
| `review-v4.js` | Unified finding interactions and manual CNV rows |
| `table-views.js` | Compact/full columns, source detail indexes and expanded tables |
| `report-igv.js` | IGV dialog, local file lifecycle and optional preservation |
| `report-attribution.js` | Attributed export/print command behavior |
| `presentation-fields.js` | Presentation text, figure references and layout fields |

`static/report.css` styles report panels, editing, tables, dialogs and print
surfaces. `templates/report/base.html` embeds validated data and panel content;
other templates define individual surfaces. Third-party IGV is bundled under
`static/igv/`, with its upstream license, and is excluded from owned-code lint.

## Extension rules

1. Add a failing behavior test at the boundary being changed.
2. Implement the smallest change in the owning layer.
3. Add contract versions/migrations when old stored documents need to remain readable.
4. Run affected tests, then the quality checks and full relevant suites.
5. Update the guide, module docstrings and generated reference if responsibilities change.

Large existing files such as `gui.py`, `html.py` and `validation.py` still
concentrate several responsibilities. New features should extract a coherent
component when that reduces complexity; do not add a second parallel state model.
