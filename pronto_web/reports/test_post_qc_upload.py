"""Late source uploads preserve saved history and reject stale or unrelated workbooks."""

import json
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings

from pronto.tests.reporting.test_post_qc_rna import NAME, RNA, row, workbook
from pronto_report.review.source_defaults import upgrade_review
from pronto_report.serialization import serialize_review_state
from pronto_web.reports.models import ReviewRevision


@override_settings(PRONTO_WORKING_DRAFTS=True)
class PostQcUploadTests(TestCase):
    def setUp(self):
        from pronto_web.reports.tests_draft_save import DraftSaveTests

        DraftSaveTests.setUp(self)
        self.record.rna_sample_ids = [RNA]
        self.record.save(update_fields=["rna_sample_ids"])
        self.draft = json.loads(serialize_review_state(upgrade_review(self.report, self.review)))
        ReviewRevision.objects.filter(report=self.record).update(review_data=self.draft)
        self.client.force_login(self.writer)
        self.upload_url = f"/reports/{self.record.pk}/post-qc-rna/"
        self.workbook_bytes = workbook()

    def upload(self, payload=None, *, token=None, client=None, filename=NAME, base=2, version=0):
        data = {
            "files": [
                SimpleUploadedFile(
                    filename,
                    payload or self.workbook_bytes,
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            ],
            "baseRevision": str(base),
            "expectedVersion": str(version),
        }
        if token is not None:
            data["previewToken"] = token
        return (client or self.client).post(self.upload_url, data)

    def apply_first(self, payload=None):
        preview = self.upload(payload)
        assert preview.status_code == 200, preview.content
        return self.upload(payload, token=preview.json()["previewToken"])

    def test_preview_apply_preserves_original_source_and_old_revision(self):
        from pronto_web.reports.models import ReportSourceRevision, WorkingDraft
        from pronto_web.reports.source_versions import load_report

        original = self.record.report_data
        preview = self.upload()
        assert preview.status_code == 200
        assert preview.json()["target"]["runId"] == self.report.run["runId"]
        assert preview.json()["target"]["sampleId"] == self.report.sample["sampleId"]
        assert preview.json()["files"][0]["rows"][0]["qc"] == "PASS"
        assert not ReportSourceRevision.objects.exists()
        applied = self.upload(token=preview.json()["previewToken"])
        assert applied.status_code == 201, applied.content
        self.record.refresh_from_db()
        assert self.record.report_data == original
        current = load_report(self.record)
        assert any(t["tableId"].startswith("postqc-") for t in current.source_tables)
        assert not any(
            t["tableId"].startswith("postqc-")
            for t in load_report(self.record, revision=1).source_tables
        )
        assert WorkingDraft.objects.get(report=self.record).review_data["schemaVersion"] == "5.0"
        source = ReportSourceRevision.objects.get(report=self.record)
        assert source.source_archive and source.actor == self.writer
        assert source.source_files[0]["name"] == NAME

    def test_stale_or_changed_bytes_and_cross_actor_tokens_fail(self):
        from pronto_web.reports.models import ReportSourceRevision

        preview = self.upload().json()
        changed = self.upload(workbook(row(QC_Verdict="FAIL")), token=preview["previewToken"])
        assert changed.status_code == 409
        self.client.force_login(self.other)
        assert self.upload(token=preview["previewToken"]).status_code == 404
        self.client.force_login(self.writer)
        assert self.upload(token=preview["previewToken"]).status_code == 201
        assert self.upload(token=preview["previewToken"]).status_code == 409
        assert ReportSourceRevision.objects.count() == 1

    def test_unlinked_sample_and_unauthenticated_requests_are_rejected(self):
        assert self.upload(client=Client()).status_code == 401
        assert self.upload(workbook(row(Sample_ID="SYN-R99"))).status_code == 422
        self.record.rna_sample_ids = []
        self.record.save(update_fields=["rna_sample_ids"])
        assert self.upload().status_code == 422

    def test_historical_page_uses_pre_upload_source(self):
        assert self.apply_first().status_code == 201
        with patch("pronto_web.reports.views.load_plot_images_from_bytes", return_value={}):
            current = self.client.get(f"/reports/{self.record.pk}/")
            previous = self.client.get(f"/reports/{self.record.pk}/?revision=1")
        assert current.status_code == previous.status_code == 200
        assert b"AKT3 (exon 1)" in current.content
        assert b"AKT3 (exon 1)" not in previous.content

    def test_rna_classification_is_saved_and_failed_qc_cannot_be_included_or_finalized(self):
        from pronto_web.reports.models import WorkingDraft

        assert self.apply_first(workbook(row(QC_Verdict="FAIL"))).status_code == 201
        working = WorkingDraft.objects.get(report=self.record)
        draft = working.review_data
        item = next(i for i in draft["findingReviews"] if i["findingId"].startswith("rna-"))
        item.update(reportingDecision="INCLUDE", clinicalClassification="ONCOGENIC")
        command = {
            "schemaVersion": "2.0",
            "reportId": self.record.pk,
            "action": "SAVE",
            "baseRevision": working.revision,
            "expectedVersion": working.version,
            "draft": draft,
        }
        url = f"/reports/{self.record.pk}/working/"
        rejected = self.client.post(url, json.dumps(command), content_type="application/json")
        assert rejected.status_code == 422
        assert rejected.json()["error"]["code"] == "RNA_QC_REQUIRED"
        # Also guard an old/invalid persisted INCLUDE on the direct finalization path.
        working.review_data = draft
        working.save(update_fields=["review_data"])
        command.update(action="FINALIZE")
        command.pop("draft")
        assert (
            self.client.post(url, json.dumps(command), content_type="application/json").status_code
            == 422
        )

    def test_passed_rna_class_saves_and_exports_the_new_source(self):
        from io import BytesIO
        from uuid import uuid4

        from pypdf import PdfReader

        from pronto_web.reports.models import WorkingDraft

        assert self.apply_first().status_code == 201
        working = WorkingDraft.objects.get(report=self.record)
        draft = working.review_data
        item = next(i for i in draft["findingReviews"] if i["findingId"].startswith("rna-"))
        item.update(reportingDecision="INCLUDE", clinicalClassification="ONCOGENIC")
        saved = self.client.post(
            f"/reports/{self.record.pk}/working/",
            json.dumps(
                {
                    "schemaVersion": "2.0",
                    "reportId": self.record.pk,
                    "action": "SAVE",
                    "baseRevision": working.revision,
                    "expectedVersion": working.version,
                    "draft": draft,
                }
            ),
            content_type="application/json",
        )
        assert saved.status_code == 201, saved.content
        exported = self.client.post(
            f"/reports/{self.record.pk}/pdf-exports/",
            json.dumps(
                {
                    "schemaVersion": "1.0",
                    "reportId": self.record.pk,
                    "revision": working.revision,
                    "workingVersion": saved.json()["workingVersion"],
                    "layout": "ESMO",
                    "requestId": str(uuid4()),
                }
            ),
            content_type="application/json",
        )
        assert exported.status_code == 200
        text = " ".join(page.extract_text() for page in PdfReader(BytesIO(exported.content)).pages)
        text = " ".join(text.split())
        assert "Oncogenic" in text and "13% read support" in text and "exon 17" in text

    def test_reopen_original_revision_restores_its_source_pair(self):
        from pronto_web.reports.models import WorkingDraft
        from pronto_web.reports.source_versions import load_report

        assert self.apply_first().status_code == 201
        working = WorkingDraft.objects.get(report=self.record)
        reopened = self.client.post(
            f"/reports/{self.record.pk}/working/",
            json.dumps(
                {
                    "schemaVersion": "2.0",
                    "reportId": self.record.pk,
                    "action": "REOPEN",
                    "baseRevision": working.revision,
                    "expectedVersion": working.version,
                    "sourceRevision": 1,
                    "replaceWorking": True,
                }
            ),
            content_type="application/json",
        )
        assert reopened.status_code == 201, reopened.content
        assert not any(
            t["tableId"].startswith("postqc-") for t in load_report(self.record).source_tables
        )
        assert any(
            t["tableId"].startswith("postqc-")
            for t in load_report(self.record, revision=working.revision).source_tables
        )

    def test_replacement_normalizes_sample_whitespace_without_retaining_old_reviews(self):
        from pronto_web.reports.models import WorkingDraft
        from pronto_web.reports.source_versions import load_report

        assert self.apply_first().status_code == 201
        working = WorkingDraft.objects.get(report=self.record)
        payload = workbook(row(Sample_ID=" " + RNA + " ", QC_Verdict="FAIL"))
        preview = self.upload(payload, base=working.revision, version=working.version)
        assert preview.status_code == 200
        applied = self.upload(
            payload,
            token=preview.json()["previewToken"],
            base=working.revision,
            version=working.version,
        )
        assert applied.status_code == 201
        tables = [t for t in load_report(self.record).source_tables if t["kind"] == "RNA"]
        assert len(tables) == 1 and len(tables[0]["rows"]) == 1
        assert not tables[0]["rows"][0]["sourceApproved"]

    def test_malformed_workbook_gets_a_safe_input_error(self):
        response = self.upload(b"not an xlsx archive")
        assert response.status_code == 422
        assert "Unreadable" in response.json()["error"]["message"]

    def test_legacy_sample_header_is_replaced_with_its_old_include_choice(self):
        from pronto_report.adapters.post_qc_rna import read_post_qc_workbook
        from pronto_web.reports.models import WorkingDraft
        from pronto_web.reports.source_versions import load_report

        table, _ = read_post_qc_workbook(self.workbook_bytes, NAME, allowed_rna_ids={RNA})
        table["tableId"] = "old-rna-table"
        table["headers"][table["headers"].index("Sample_ID")] = "Sample_id"
        table["rows"][0].pop("sourceSampleId", None)
        table["rows"][0].update(findingId="old-finding", occurrenceId="old-finding:1")
        self.record.report_data["sourceTables"].append(table)
        self.record.save(update_fields=["report_data"])
        self.draft["findingReviews"] = [
            {"findingId": "old-finding", "reportingDecision": "INCLUDE", "reportHighlight": True}
        ]
        ReviewRevision.objects.filter(report=self.record).update(review_data=self.draft)
        assert self.apply_first().status_code == 201
        assert len([t for t in load_report(self.record).source_tables if t["kind"] == "RNA"]) == 1
        assert all(
            item["findingId"] != "old-finding"
            for item in WorkingDraft.objects.get(report=self.record).review_data["findingReviews"]
        )

    def test_missing_private_linkage_archive_returns_input_error(self):
        from tempfile import TemporaryDirectory

        from pronto_web.reports.models import ImportBatch, ImportItem, ImportSource

        self.record.rna_sample_ids = []
        self.record.save(update_fields=["rna_sample_ids"])
        item = ImportItem.objects.create(
            batch=ImportBatch.objects.create(actor=self.writer),
            report=self.record,
            sample_id=self.report.sample["sampleId"],
            run_id=self.report.run["runId"],
            status="imported",
        )
        ImportSource.objects.create(
            item=item,
            role="sample_list",
            original_name="sample_list.tsv",
            archive_key="absent/sample_list.tsv",
            sha256="0" * 64,
            size_bytes=0,
        )
        with TemporaryDirectory() as archive, self.settings(PRONTO_RAW_IMPORT_ROOT=archive):
            response = self.upload()
        assert response.status_code == 422

    def test_page_binds_sources_after_a_concurrent_post_qc_commit(self):
        from pronto_web.reports.working_drafts import current_working

        interleaved = False

        def current_after_upload(record, report):
            nonlocal interleaved
            if not interleaved:
                interleaved = True
                assert self.apply_first().status_code == 201
            return current_working(record, report)

        with (
            patch(
                "pronto_web.reports.working_drafts.current_working",
                side_effect=current_after_upload,
            ),
            patch("pronto_web.reports.views.load_plot_images_from_bytes", return_value={}),
        ):
            response = self.client.get(f"/reports/{self.record.pk}/")
        assert response.status_code == 200
        assert b"AKT3 (exon 1)" in response.content

    def test_export_freeze_does_not_deduplicate_different_source_facts(self):
        from pronto_web.reports.models import ReportSourceRevision, WorkingDraft
        from pronto_web.reports.working_drafts import freeze_draft

        same_review = {**self.draft, "revision": 2}
        WorkingDraft.objects.create(
            report=self.record, revision=2, version=1, review_data=same_review
        )
        facts = {
            **self.record.report_data,
            "diagnostics": [
                *self.record.report_data["diagnostics"],
                {
                    "code": "CHANGED_FACT",
                    "severity": "INFO",
                    "message": "Synthetic source update",
                    "path": "sourceTables",
                },
            ],
        }
        ReportSourceRevision.objects.create(
            report=self.record, effective_revision=2, report_data=facts, actor=self.writer
        )
        advanced = freeze_draft(self.record, 2, 1)
        assert advanced[2] == 2
        assert ReviewRevision.objects.filter(report=self.record, revision=2).exists()

    def test_separate_fusion_and_splice_files_can_have_the_same_filename(self):
        from io import BytesIO
        from zipfile import ZipFile

        from pronto_web.reports.models import ReportSourceRevision
        from pronto_web.reports.source_versions import load_report

        splice = workbook(
            row(
                Provisional_Event_Type="Splice_variant",
                Gene_A="MET",
                Gene_B="MET",
                Exon_A=13,
                Exon_B=15,
                Event_ID="MET:chr7:100:MET:chr7:200",
            )
        )

        def submit(token=None):
            data = {
                "files": [
                    SimpleUploadedFile(NAME, self.workbook_bytes),
                    SimpleUploadedFile(NAME, splice),
                ],
                "baseRevision": "2",
                "expectedVersion": "0",
            }
            if token:
                data["previewToken"] = token
            return self.client.post(self.upload_url, data)

        preview = submit()
        assert preview.status_code == 200
        assert {item["kind"] for item in preview.json()["replacementScope"]} == {
            "Fusion",
            "Splice_variant",
        }
        assert submit(preview.json()["previewToken"]).status_code == 201
        tables = [
            table for table in load_report(self.record).source_tables if table["kind"] == "RNA"
        ]
        assert len(tables) == 2
        assert len({table["tableId"] for table in tables}) == 2
        assert len({table["rows"][0]["findingId"] for table in tables}) == 2
        source = ReportSourceRevision.objects.get(report=self.record)
        with ZipFile(BytesIO(source.source_archive)) as archive:
            assert archive.read("0/" + NAME) == self.workbook_bytes
            assert archive.read("1/" + NAME) == splice
