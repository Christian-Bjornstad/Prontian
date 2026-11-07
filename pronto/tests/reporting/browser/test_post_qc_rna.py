"""Real Chromium checks for post-QC preview, clinical classification and read-only history."""

import json
from pathlib import Path

from pronto.tests.reporting.browser.test_report import _serve, playwright
from pronto.tests.reporting.test_html_review_state import draft_review
from pronto.tests.reporting.test_post_qc_rna import NAME, RNA, row, workbook
from pronto.tests.reporting.test_pronto_output_adapter import build_report
from pronto_report.adapters.post_qc_rna import read_post_qc_workbook
from pronto_report.renderers.html import render_html
from pronto_report.review.source_defaults import upgrade_review
from pronto_report.serialization import serialize_report_data, serialize_review_state
from pronto_report.validation import validate_report_data, validate_review_state


def rna_case():
    table, _ = read_post_qc_workbook(
        workbook(row(), row(QC_Verdict="FAIL", Event_ID="SYN-failed-event")),
        NAME,
        allowed_rna_ids={RNA},
    )
    document = json.loads(serialize_report_data(build_report()))
    document["sourceTables"].append(table)
    report = validate_report_data(document)
    draft = json.loads(serialize_review_state(upgrade_review(report, draft_review(report))))
    draft["schemaVersion"] = "5.0"
    return report, validate_review_state(draft, report=report)


def test_rna_class_include_and_download_keep_v5_and_guard_failed_qc(browser, tmp_path):
    report, review = rna_case()
    with _serve(render_html(report, review, inline_assets=True)) as url:
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            page.goto(url)
            page.get_by_role("button", name="Edit mode: OFF").click()
            page.get_by_role("tab", name="RNA review", exact=True).click()
            rows = page.locator('tr[data-source-kind="RNA"]')
            assert rows.count() == 2
            rows.nth(0).locator("[data-rna-class]").select_option("ONCOGENIC")
            rows.nth(0).locator('[data-source-action="INCLUDE"]').click()
            assert rows.nth(1).locator('[data-source-action="INCLUDE"]').is_disabled()
            assert "AKT3 (exon 1)::CEP112 (exon 17)" in rows.nth(0).inner_text()
            page.get_by_role("tab", name="Variant review").click()
            with page.expect_download() as pending:
                page.get_by_role("button", name="Download ReviewState", exact=True).click()
            saved = json.loads(Path(pending.value.path()).read_text(encoding="utf-8"))
            assert saved["schemaVersion"] == "5.0"
            chosen = next(
                item for item in saved["findingReviews"] if item["reportingDecision"] == "INCLUDE"
            )
            assert chosen["clinicalClassification"] == "ONCOGENIC"
            assert not errors
        finally:
            context.close()


def test_preview_discloses_reversed_columns_and_sends_confirmed_bytes(browser, tmp_path):
    report, review = rna_case()
    html = render_html(
        report,
        review,
        inline_assets=True,
        save_url="/working/",
        csrf_token="synthetic-csrf",
        actor_id="1",
        actor_label="writer",
        post_qc_upload_url="/post-qc/",
    )
    calls = []
    payload = workbook(row(Outcome="OK", QC_Verdict="out of frame"))
    table, preview = read_post_qc_workbook(payload, NAME, allowed_rna_ids={RNA})

    def upload(route):
        calls.append(route.request.post_data_buffer)
        route.fulfill(
            json={
                "files": [{"name": NAME, "sha256": table["sha256"], "rows": preview}],
                "replacementScope": [{"sampleId": RNA, "kind": "Fusion"}],
                "previewToken": "synthetic-preview-token",
            }
        )

    with _serve(html) as url:
        context = browser.new_context()
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        try:
            page.route("**/post-qc/", upload)
            page.goto(url)
            page.get_by_role("tab", name="RNA review", exact=True).click()
            page.locator("#post-qc-files").set_input_files(
                {
                    "name": NAME,
                    "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "buffer": payload,
                }
            )
            page.get_by_role("button", name="Preview post-QC files", exact=True).click()
            preview_panel = page.locator("[data-post-qc-preview]")
            playwright.expect(preview_panel).to_contain_text("Reversed: Outcome contains QC")
            assert (
                "PASS" in preview_panel.inner_text()
                and "out-of-frame" in preview_panel.inner_text()
            )
            assert len(calls) == 1 and payload in calls[0]
            assert b"previewToken" not in calls[0]
            assert page.get_by_role(
                "button", name="Import confirmed post-QC files", exact=True
            ).is_visible()
            page.screenshot(path=str(tmp_path / "post-qc-preview.png"), full_page=True)
            # A different selection invalidates the previous confirmation immediately.
            page.locator("#post-qc-files").set_input_files([])
            assert page.get_by_role(
                "button", name="Import confirmed post-QC files", exact=True
            ).is_hidden()
            assert not errors
        finally:
            context.close()
