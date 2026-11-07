"""Server-side RNA eligibility guards shared by save, finalize and export paths."""

from pronto_report.adapters.post_qc_rna import technical_qc

from .contracts import ReviewCommandError


def validate_rna_review(report, review):
    """Clinical labels belong to RNA findings; post-QC INCLUDE requires explicit PASS.

    This is independent of UI controls and source highlight colors. Checking
    every transition also protects direct finalization of a persisted draft.
    """
    rna_ids, ineligible = set(), set()
    for table in report.source_tables:
        if table["kind"] != "RNA":
            continue
        for row in table["rows"]:
            rna_ids.add(row["findingId"])
            if (
                table["tableId"].startswith("postqc-")
                and technical_qc(dict(zip(table["headers"], row["values"])))[0] != "PASS"
            ):
                ineligible.add(row["findingId"])
    for item in review.finding_reviews:
        if "clinicalClassification" in item and item["findingId"] not in rna_ids:
            raise ReviewCommandError(
                "INVALID_DRAFT", "RNA clinical class requires an RNA finding", 422
            )
        if item["findingId"] in ineligible and item["reportingDecision"] == "INCLUDE":
            raise ReviewCommandError(
                "RNA_QC_REQUIRED", "Only technically passed post-QC RNA events may be included", 422
            )
