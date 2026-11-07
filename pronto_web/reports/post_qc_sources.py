"""Compose a new source/review pair without modifying earlier report snapshots."""

import json
from copy import deepcopy

from pronto_report.adapters.post_qc_rna import event_kind, sample_identity
from pronto_report.review.source_defaults import upgrade_review
from pronto_report.serialization import serialize_report_data, serialize_review_state
from pronto_report.validation import validate_report_data, validate_review_state


def replacement_scope(tables):
    """The confirmation applies to the exact sample/event categories present in the files."""
    return {
        (sample_identity(fields), event_kind(fields))
        for table in tables
        for row in table["rows"]
        for fields in [dict(zip(table["headers"], row["values"]))]
    }


def compose_sources(report, review, tables, *, revision, actor, timestamp):
    """Replace only the confirmed RNA scope and reset its human review for reassessment.

    Unaffected source/review rows and notes survive. Replaced candidates always
    start UNREVIEWED, even if a stable event ID reappears with changed QC. All
    raw cells, including failed candidates, remain in the new source snapshot.
    """
    document = json.loads(serialize_report_data(report))
    scopes = replacement_scope(tables)
    removed, retained = set(), []
    for table in document.get("sourceTables", []):
        if table["kind"] != "RNA":
            retained.append(table)
            continue
        rows = []
        for row in table["rows"]:
            fields = dict(zip(table["headers"], row["values"]))
            identity = (
                sample_identity(fields, row.get("sourceSampleId")),
                event_kind(fields),
            )
            if identity in scopes:
                removed.add(row["findingId"])
            else:
                rows.append(row)
        if rows:
            table["rows"] = rows
            retained.append(table)
    document["sourceTables"] = retained + deepcopy(tables)
    source_names = {
        (item["name"], item["sha256"]) for item in document["provenance"]["sourceFiles"]
    }
    for table in tables:
        if (table["fileName"], table["sha256"]) not in source_names:
            document["provenance"]["sourceFiles"].append(
                {"name": table["fileName"], "sha256": table["sha256"]}
            )
    document["diagnostics"].append(
        {
            "code": "POST_QC_RNA",
            "severity": "INFO",
            "path": "sourceTables",
            "message": "Manually confirmed post-QC RNA sources. Technical QC is independent of clinical classification; replaced RNA findings require fresh review.",
        }
    )
    source = validate_report_data(document)
    draft = json.loads(serialize_review_state(upgrade_review(report, review)))
    draft.update(
        schemaVersion="5.0",
        revision=revision,
        updatedAt=timestamp,
        reviewer={"reviewerId": str(actor.pk)},
    )
    draft["lastSavedAttribution"] = {
        "actorId": str(actor.pk),
        "actorLabel": actor.get_username(),
        "method": "AUTHENTICATED",
    }
    new_ids = {row["findingId"] for table in tables for row in table["rows"]}
    draft["findingReviews"] = [
        item for item in draft["findingReviews"] if item["findingId"] not in removed | new_ids
    ]
    draft["findingReviews"].extend(
        {
            "findingId": row["findingId"],
            "reportingDecision": "UNREVIEWED",
            "reportHighlight": False,
            "clinicalClassification": "UNCLASSIFIED",
        }
        for table in tables
        for row in table["rows"]
    )
    draft["sectionQc"]["rna"] = {"status": "NOT_REVIEWED"}
    return source, validate_review_state(draft, report=source)
