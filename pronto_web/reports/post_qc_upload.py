"""Two-step private post-QC upload: preview exact facts, then compare-and-swap apply."""

import json
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.core import signing
from django.db import IntegrityError, OperationalError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from pronto_report.adapters.post_qc_rna import PostQcProblem, read_post_qc_workbook
from pronto_report.serialization import serialize_report_data, serialize_review_state
from pronto_report.validation import validate_review_state

from .models import (
    ReportGrant,
    ReportRecord,
    ReportSourceRevision,
    ReviewRevision,
    WorkingDraft,
    WorkingDraftEvent,
)
from .post_qc_sources import compose_sources, replacement_scope
from .source_versions import linked_rna_ids, load_report, source_key
from .working_drafts import current_working

MAX_BYTES = 25 * 1024 * 1024
SALT = "prontian.post-qc-preview.v1"


def _error(code, message, status):
    return JsonResponse({"error": {"code": code, "message": message}}, status=status)


def _current(record, report):
    if settings.PRONTO_WORKING_DRAFTS:
        return current_working(record, report)
    latest = record.reviews.order_by("-revision").first()
    return (validate_review_state(latest.review_data, report=report) if latest else None), 0


@never_cache
@require_POST
@csrf_protect
def post_qc_rna(request, report_id):
    """Authorize before parsing, bind confirmation to bytes/actor/source/draft, then append.

    Preview does not persist files. The browser resends the selected bytes with
    a signed 15-minute token; changed files or a concurrently edited draft must
    be previewed again. Final reports must be reopened before adding sources.
    """
    if not request.user.is_authenticated or not request.user.is_active:
        return _error("UNAUTHENTICATED", "Sign in before importing post-QC sources.", 401)
    grant = get_object_or_404(
        ReportGrant.objects.select_related("report"), report_id=report_id, user=request.user
    )
    try:
        uploads = request.FILES.getlist("files")
        if not 1 <= len(uploads) <= 10 or sum(item.size for item in uploads) > MAX_BYTES:
            return _error("UPLOAD_LIMIT", "Select 1–10 workbooks, at most 25 MiB together.", 413)
        base, expected = int(request.POST["baseRevision"]), int(request.POST["expectedVersion"])
        tables, previews, files = [], [], []
        try:
            allowed = linked_rna_ids(grant.report)
        except ValueError as error:
            return _error("RNA_LINKAGE_UNAVAILABLE", str(error), 422)
        for upload in uploads:
            payload = upload.read(MAX_BYTES + 1)
            table, rows = read_post_qc_workbook(payload, upload.name, allowed_rna_ids=allowed)
            tables.append(table)
            previews.append({"name": upload.name, "sha256": table["sha256"], "rows": rows})
            files.append((upload.name, payload, table["sha256"]))
        scopes = [replacement_scope([table]) for table in tables]
        if any(first & second for i, first in enumerate(scopes) for second in scopes[i + 1 :]):
            return _error(
                "OVERLAPPING_SOURCES",
                "Select one workbook per RNA sample/event category; competing sources were not imported.",
                422,
            )
        with transaction.atomic():
            record = ReportRecord.objects.select_for_update().get(pk=report_id)
            if not ReportGrant.objects.filter(
                report=record, user=request.user, user__is_active=True
            ).exists():
                return _error("FORBIDDEN", "Report access is unavailable.", 403)
            report = load_report(record)
            current, version = _current(record, report)
            if current is None or current.status != "DRAFT":
                return _error(
                    "FINAL_LOCKED", "Start a new draft revision before adding post-QC files.", 409
                )
            if (current.revision, version) != (base, expected):
                return _error(
                    "REVISION_CONFLICT", "The draft changed. Reload and preview again.", 409
                )
            identity = {
                "report": report_id,
                "actor": request.user.pk,
                "revision": base,
                "version": expected,
                "source": source_key(record, base),
                "rna": sorted(allowed),
                "files": [[name, digest] for name, _, digest in files],
            }
            token = request.POST.get("previewToken")
            if not token:
                return JsonResponse(
                    {
                        "target": {
                            "reportId": report_id,
                            "sampleId": report.sample["sampleId"],
                            "runId": report.run["runId"],
                        },
                        "files": previews,
                        "replacementScope": [
                            {"sampleId": sample, "kind": kind}
                            for sample, kind in sorted(replacement_scope(tables))
                        ],
                        "previewToken": signing.dumps(identity, salt=SALT),
                    }
                )
            if signing.loads(token, salt=SALT, max_age=900) != identity:
                return _error("PREVIEW_CHANGED", "The files or draft changed. Preview again.", 409)
            archive_sizes = record.source_revisions.values_list("source_files", flat=True)
            if (
                record.source_revisions.count() >= 100
                or sum(item.get("sizeBytes", 0) for group in archive_sizes for item in group)
                + sum(len(payload) for _, payload, _ in files)
                > 64 * 1024 * 1024
            ):
                return _error("ARCHIVE_LIMIT", "This report's post-QC source archive is full.", 413)
            # Preserve the current working facts/choices before changing sources.
            previous = json.loads(serialize_review_state(current))
            saved, created = ReviewRevision.objects.get_or_create(
                report=record, revision=base, defaults={"review_data": previous}
            )
            if not created and saved.review_data != previous:
                return _error(
                    "REVISION_CONFLICT", "The saved revision changed. Reload before importing.", 409
                )
            revision = max(base, record.reviews.order_by("-revision").first().revision) + 1
            now = timezone.now()
            source, review = compose_sources(
                report,
                current,
                tables,
                revision=revision,
                actor=request.user,
                timestamp=now.isoformat(),
            )
            archive = BytesIO()
            with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
                for index, (name, payload, _) in enumerate(files):
                    bundle.writestr(f"{index}/{name}", payload)
            ReportSourceRevision.objects.create(
                report=record,
                effective_revision=revision,
                report_data=json.loads(serialize_report_data(source)),
                source_files=[
                    {"name": name, "sha256": digest, "sizeBytes": len(payload)}
                    for name, payload, digest in files
                ],
                source_archive=archive.getvalue(),
                actor=request.user,
            )
            document = json.loads(serialize_review_state(review))
            if settings.PRONTO_WORKING_DRAFTS:
                WorkingDraft.objects.update_or_create(
                    report=record,
                    defaults={
                        "revision": revision,
                        "version": version + 1,
                        "review_data": document,
                        "source_revision": base,
                    },
                )
                WorkingDraftEvent.objects.create(
                    report=record,
                    actor=request.user,
                    action="POST_QC_IMPORT",
                    revision=revision,
                    version=version + 1,
                    source_revision=base,
                    occurred_at=now,
                )
            else:
                ReviewRevision.objects.create(
                    report=record, revision=revision, review_data=document
                )
        return JsonResponse(
            {
                "revision": revision,
                "workingVersion": version + 1 if settings.PRONTO_WORKING_DRAFTS else 0,
            },
            status=201,
        )
    except signing.BadSignature:
        return _error(
            "PREVIEW_EXPIRED", "The preview is invalid or expired. Preview the files again.", 409
        )
    except PostQcProblem as error:
        return _error("INVALID_POST_QC", str(error), 422)
    except KeyError, ValueError:
        return _error(
            "INVALID_POST_QC",
            "Check the exact RNA linkage, filename, required columns and unique event rows. No source changes were applied.",
            422,
        )
    except IntegrityError, OperationalError:
        return _error(
            "REVISION_CONFLICT",
            "Another operation changed this report. Reload and preview again.",
            409,
        )
    except OSError:
        return _error(
            "SOURCE_STORAGE_UNAVAILABLE",
            "The private source archive or temporary upload storage is unavailable. Restore access before retrying.",
            503,
        )
