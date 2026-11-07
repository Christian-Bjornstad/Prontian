"""Resolve immutable report source versions and verified historical DNA/RNA linkage."""

import json
from hashlib import sha256
from pathlib import Path

from django.conf import settings

from pronto_report.serialization import serialize_report_data
from pronto_report.validation import validate_report_data

from .models import ImportSource, ReportSourceRevision


def load_report(record, *, revision=None):
    """Bind current or historical review to the source facts effective at that revision."""
    versions = record.source_revisions.all()
    if revision is not None:
        versions = versions.filter(effective_revision__lte=revision)
    version = versions.order_by("-effective_revision").first()
    report = validate_report_data(version.report_data if version else record.report_data)
    if report.report_id != record.pk:
        raise ValueError("Stored report source identity mismatch")
    return report


def source_key(record, revision):
    """Compare facts, not review JSON, when deduplicating frozen export revisions."""
    return sha256(serialize_report_data(load_report(record, revision=revision))).hexdigest()


def bind_restored_source(record, source_revision, target_revision, actor):
    """A reopened historical review retains its historical source facts as well as choices.

    Called within the report-locked transaction. An explicit new binding can
    restore the original base document after a newer post-QC source was added.
    Raw uploaded workbooks remain in their original source-version archive.
    """
    if record.source_revisions.exists():
        ReportSourceRevision.objects.create(
            report=record,
            effective_revision=target_revision,
            report_data=json.loads(
                serialize_report_data(load_report(record, revision=source_revision))
            ),
            actor=actor,
        )


def linked_rna_ids(record):
    """Use imported exact linkage; never infer RNA identity from a DNA ID prefix.

    New imports store the validated IDs directly. Existing imports can recover
    the same claims from hash-verified private archived sources, allowing an
    upgrade without reimporting or changing any original source document.
    """
    from pronto_ingest.discovery import MAX_BYTES, regular_file
    from pronto_ingest.linkage import _ID, resolve_links
    from pronto_report.adapters.post_qc_rna import sample_identity

    if record.rna_sample_ids:
        if not isinstance(record.rna_sample_ids, list) or any(
            not isinstance(value, str) or not _ID.fullmatch(value)
            for value in record.rna_sample_ids
        ):
            raise ValueError("Stored RNA linkage is invalid")
        return set(record.rna_sample_ids)
    report = validate_report_data(record.report_data)
    identifiers = {
        sample_identity(dict(zip(table["headers"], row["values"])), row.get("sourceSampleId"))
        for table in report.source_tables
        if table["kind"] == "RNA" and not table["demo"]
        for row in table["rows"]
        if sample_identity(dict(zip(table["headers"], row["values"])), row.get("sourceSampleId"))
    }
    if identifiers:
        return identifiers
    root_value = getattr(settings, "PRONTO_RAW_IMPORT_ROOT", "")
    if not root_value:
        raise ValueError(
            "Original DNA/RNA linkage is unavailable; open this report in the desktop installation with its private source archive"
        )
    root = Path(root_value).absolute()
    sources = {}
    items = set()
    for source in ImportSource.objects.filter(
        item__report=record,
        item__status="imported",
        role__in=["sample_list", "linkage", "variants"],
    ):
        relative = Path(source.archive_key)
        path = root / relative
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not path.resolve().is_relative_to(root.resolve())
        ):
            raise ValueError("Invalid archived linkage path")
        try:
            if not regular_file(path) or path.stat().st_size > MAX_BYTES:
                raise ValueError("Archived DNA/RNA linkage is inaccessible")
            if sha256(path.read_bytes()).hexdigest() != source.sha256:
                raise ValueError("Archived DNA/RNA linkage checksum mismatch")
        except OSError:
            raise ValueError(
                "Archived DNA/RNA linkage is inaccessible; restore the original private source archive"
            ) from None
        sources.setdefault(source.role, []).append(path)
        items.add(source.item_id)
    if len(items) != 1 or not sources:
        raise ValueError("No unambiguous archived DNA/RNA linkage is available")
    try:
        return resolve_links(str(report.sample["sampleId"]), sources) - {
            str(report.sample["sampleId"])
        }
    except OSError:
        raise ValueError(
            "Archived DNA/RNA linkage could not be read; restore the private source archive"
        ) from None
