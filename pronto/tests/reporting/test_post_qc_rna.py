"""Synthetic post-QC workbooks preserve raw facts and require exact RNA identity."""

from io import BytesIO

import pytest
from openpyxl import Workbook
from openpyxl.styles import PatternFill

from pronto_report.adapters.post_qc_rna import read_post_qc_workbook

RNA = "SYN-R01"
NAME = RNA + "_fusion_and_splice_variant_candidates.xlsx"
HEADERS = [
    "Provisional_Event_Type",
    "Event_type",
    "Sample_ID",
    "Gene_A",
    "Gene_B",
    "Exon_A",
    "Exon_B",
    "Event_Support_Dedup_Percentage",
    "Outcome",
    "QC_Verdict",
    "Provisional_Event_ID",
    "Event_ID",
]


def workbook(*rows):
    book = Workbook()
    sheet = book.active
    sheet.title = "Candidates"
    sheet.append(["# Synthetic source, no patient data"])
    sheet.append(HEADERS)
    for values in rows or [row()]:
        sheet.append(values)
    # Color intentionally contradicts QC: it must never authorize a failed row.
    for cell in sheet[3]:
        cell.fill = PatternFill("solid", fgColor="FFFF00")
    output = BytesIO()
    book.save(output)
    book.close()
    return output.getvalue()


def row(**changes):
    values = dict(
        zip(
            HEADERS,
            [
                "Fusion",
                ".",
                RNA,
                "AKT3",
                "CEP112",
                1,
                17,
                12.676,
                "out-of-frame",
                "PASS",
                "AKT3:chr1:100:CEP112:chr17:200",
                "AKT3:chr1:100:CEP112:chr17:201",
            ],
        )
    )
    values.update(changes)
    return [values[header] for header in HEADERS]


def test_standard_and_reversed_columns_have_same_preview_but_keep_raw_cells():
    standard = read_post_qc_workbook(workbook(), NAME, allowed_rna_ids={RNA})
    reversed_ = read_post_qc_workbook(
        workbook(row(Outcome="OK", QC_Verdict="out of frame")), NAME, allowed_rna_ids={RNA}
    )
    for table, preview in (standard, reversed_):
        assert preview[0]["label"] == "AKT3 (exon 1)::CEP112 (exon 17)"
        assert preview[0]["reportLabel"] == (
            "AKT3 (exon 1)::CEP112 (exon 17), 13% read support, out-of-frame"
        )
        assert preview[0]["qc"] == "PASS"
        assert table["rows"][0]["sourceApproved"] is True
    assert standard[1][0]["columnsSwapped"] is False
    assert reversed_[1][0]["columnsSwapped"] is True
    assert reversed_[0]["rows"][0]["values"][HEADERS.index("Outcome")] == "OK"


def test_color_does_not_make_a_fail_or_unreviewed_event_pass():
    for qc in ("FAIL", ".", "novel-value"):
        table, preview = read_post_qc_workbook(
            workbook(row(QC_Verdict=qc)), NAME, allowed_rna_ids={RNA}
        )
        assert not table["rows"][0]["sourceApproved"]
        assert preview[0]["qc"] in {"FAIL", "NOT_REVIEWED", "UNKNOWN"}


def test_candidate_identity_survives_filename_change_but_distinguishes_event_category():
    first, _ = read_post_qc_workbook(workbook(), NAME, allowed_rna_ids={RNA})
    renamed, _ = read_post_qc_workbook(
        workbook(), NAME.replace(".xlsx", "_withQC.xlsx"), allowed_rna_ids={RNA}
    )
    splice, _ = read_post_qc_workbook(
        workbook(row(Provisional_Event_Type="Splice_variant")), NAME, allowed_rna_ids={RNA}
    )
    assert first["rows"][0]["findingId"] == renamed["rows"][0]["findingId"]
    assert first["rows"][0]["findingId"] != splice["rows"][0]["findingId"]


@pytest.mark.parametrize(
    "values,name",
    [
        (row(Sample_ID="SYN-R02"), NAME),
        (row(), "SYN-R02_fusion_and_splice_variant_candidates.xlsx"),
        (row(Provisional_Event_Type="Unknown"), NAME),
    ],
)
def test_rejects_wrong_sample_filename_or_unknown_event(values, name):
    with pytest.raises(ValueError):
        read_post_qc_workbook(workbook(values), name, allowed_rna_ids={RNA})


def test_mixed_samples_and_duplicate_events_are_not_silently_filtered():
    for rows in ((row(), row(Sample_ID="SYN-R02")), (row(), row())):
        with pytest.raises(ValueError):
            read_post_qc_workbook(workbook(*rows), NAME, allowed_rna_ids={RNA})
