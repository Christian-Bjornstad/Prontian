"""Bounded post-QC RNA workbooks: exact identity, raw facts and explicit QC mapping."""

import json
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from .source_tables import MAX_BYTES, read_source_table

REQUIRED_HEADERS = {
    "Sample_ID",
    "Gene_A",
    "Gene_B",
    "Exon_A",
    "Exon_B",
    "Provisional_Event_Type",
    "Event_Support_Dedup_Percentage",
    "Outcome",
    "QC_Verdict",
}
OUTCOMES = {
    "in-frame": "in-frame",
    "out-of-frame": "out-of-frame",
    "truncated-loss": "truncated-loss",
    "unknown": "unknown",
}
QC = {"pass": "PASS", "ok": "PASS", "fail": "FAIL"}
EMPTY = {"", ".", "n/a", "na", "none"}


class PostQcProblem(ValueError):
    """Fixed, safe input diagnostic; never exposes parser cells or workstation paths."""


def _text(value):
    return "" if value is None or str(value).strip().casefold() in EMPTY else str(value).strip()


def event_kind(fields):
    """Use the final declared event type when present, otherwise the provisional type."""
    value = (
        _text(fields.get("Event_Type"))
        or _text(fields.get("Event_type"))
        or _text(fields.get("Provisional_Event_Type"))
    )
    return {"fusion": "Fusion", "splice_variant": "Splice_variant"}.get(value.casefold())


def sample_identity(fields, source_sample_id=None):
    """Resolve the exact RNA claim across established source-header spellings.

    Whitespace is normalized consistently for preview and replacement scope;
    two conflicting nonempty identity columns are rejected, never preferred.
    """
    values = {
        _text(fields.get(key))
        for key in ("Sample_ID", "Sample_id", "sample_id", "sample_ID")
        if _text(fields.get(key))
    }
    if _text(source_sample_id):
        values.add(_text(source_sample_id))
    if len(values) > 1:
        raise PostQcProblem("Conflicting RNA sample identity columns")
    return next(iter(values), "")


def technical_qc(fields):
    """Interpret only the documented standard or recognized reversed QC/consequence pair.

    Source cells are never rewritten. Empty and unfamiliar verdicts remain
    ineligible; spreadsheet highlight colors do not participate in this rule.
    """
    outcome, verdict = _text(fields.get("Outcome")), _text(fields.get("QC_Verdict"))
    normalized_outcome = re.sub(r"[\s_]+", "-", outcome.casefold())
    normalized_verdict = re.sub(r"[\s_]+", "-", verdict.casefold())
    swapped = outcome.casefold() in QC and normalized_verdict in OUTCOMES
    if swapped:
        outcome, verdict = verdict, outcome
        normalized_outcome = normalized_verdict
    status = QC.get(verdict.casefold(), "NOT_REVIEWED" if not verdict else "UNKNOWN")
    return status, OUTCOMES.get(normalized_outcome, outcome), swapped


def nomenclature(fields):
    """Format declared partner/exon labels without inferring an exon-skipping event."""

    def partner(gene_key, exon_key):
        gene, exon = _text(fields.get(gene_key)), _text(fields.get(exon_key))
        exon = re.sub(r"(?:\.0)$", "", exon)
        if not gene:
            return ""
        if re.fullmatch(r"\d+", exon):
            exon = "exon " + exon
        elif re.fullmatch(r"ex\d+", exon, re.IGNORECASE):
            exon = "exon " + exon[2:]
        return f"{gene} ({exon})" if exon else gene

    return "::".join(filter(None, [partner("Gene_A", "Exon_A"), partner("Gene_B", "Exon_B")]))


def support_label(fields):
    """Round a percentage for report copy; the exact original value stays in the table."""
    raw = _text(fields.get("Event_Support_Dedup_Percentage")).removesuffix("%")
    if not raw:
        return ""
    try:
        value = Decimal(raw.replace(",", "."))
        if not value.is_finite() or not 0 <= value <= 100:
            raise PostQcProblem("Read support must be a percentage from 0 to 100")
        return f"{value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)}%"
    except InvalidOperation:
        raise PostQcProblem("Read support must be a numeric percentage") from None


def preview_row(fields):
    """Return normalized display facts plus the disclosed source-column interpretation."""
    qc, outcome, swapped = technical_qc(fields)
    label, support = nomenclature(fields), support_label(fields)
    return {
        "sampleId": sample_identity(fields),
        "kind": event_kind(fields),
        "label": label,
        "support": support,
        "rawSupport": fields.get("Event_Support_Dedup_Percentage"),
        "outcome": outcome,
        "qc": qc,
        "columnsSwapped": swapped,
        "reportLabel": ", ".join(
            filter(None, [label, support + " read support" if support else "", outcome])
        ),
    }


def read_post_qc_workbook(payload, filename, *, allowed_rna_ids):
    """Read a selected workbook, rejecting mixed/unlinked samples and duplicate events.

    Filenames must declare the same exact RNA ID as every source row. Event IDs
    are independent of filename and worksheet; byte checksums separately track
    changes to QC, read support and other facts. Return the untouched source
    cells and a human-readable preview, including FAIL/unreviewed candidates.
    """
    if len(payload) > MAX_BYTES or not allowed_rna_ids:
        raise PostQcProblem("Post-QC file is too large or the imported RNA linkage is unavailable")
    match = re.fullmatch(
        r"([A-Za-z0-9][A-Za-z0-9._:-]{0,127})_fusion_and_splice_variant_candidates(?:_withQC)?\.xlsx",
        filename,
        re.IGNORECASE,
    )
    if not match or match[1] not in allowed_rna_ids:
        raise PostQcProblem("Filename does not identify an exactly linked RNA sample")
    with TemporaryDirectory(prefix="prontian-postqc-") as temporary:
        path = Path(temporary) / "source.xlsx"
        path.write_bytes(payload)
        try:
            table = read_source_table(path, kind="RNA")
        except Exception as error:
            raise PostQcProblem(
                "Unreadable or oversized XLSX workbook; select one worksheet with literal post-QC values"
            ) from error
    table["fileName"] = filename
    if not REQUIRED_HEADERS <= set(table["headers"]) or len(set(table["headers"])) != len(
        table["headers"]
    ):
        raise PostQcProblem("Missing or duplicate post-QC column headers")
    if not table["rows"]:
        raise PostQcProblem(
            "Empty workbooks require an explicit replacement scope; no sources were changed"
        )
    table["tableId"] = "postqc-" + sha256((filename + table["sha256"]).encode()).hexdigest()[:24]
    previews, identities = [], set()
    for row in table["rows"]:
        fields = dict(zip(table["headers"], row["values"]))
        if sample_identity(fields) != match[1]:
            raise PostQcProblem(
                "Workbook rows do not all belong to the exact RNA sample in the filename"
            )
        preview = preview_row(fields)
        if (
            not preview["kind"]
            or not _text(fields.get("Gene_A"))
            or not _text(fields.get("Gene_B"))
        ):
            raise PostQcProblem("Unknown event category or missing gene partner")
        event = _text(fields.get("Event_ID")) or _text(fields.get("Provisional_Event_ID"))
        if not event:
            raise PostQcProblem("Post-QC row requires an explicit event identity")
        identity = json.dumps([match[1], preview["kind"], event], separators=(",", ":"))
        if identity in identities:
            raise PostQcProblem("Duplicate RNA event in the selected workbook")
        identities.add(identity)
        row["findingId"] = "rna-" + sha256(identity.encode()).hexdigest()[:24]
        row["occurrenceId"] = row["findingId"] + ":1"
        row["sourceApproved"] = preview["qc"] == "PASS"
        previews.append({"findingId": row["findingId"], **preview})
    return table, previews
