"""Keep source-to-contract-to-HTML parity after retiring the legacy PPTX golden."""

from pathlib import Path

from pronto.tests.reporting.test_pronto_output_adapter import build_report
from pronto_report.adapters.text_tables import read_text_rows
from pronto_report.renderers.html import render_html

FIXTURE = (
    Path(__file__).parents[3]
    / "test_data/ous/251114_A02134_0115_BHCJCKDRX7_TSO_500_LocalApp_postprocessing_results"
)


def test_approved_source_contract_and_html_preserve_biomarker_and_case_facts():
    report = build_report()
    html = render_html(report, inline_assets=True)
    metadata = read_text_rows(FIXTURE / "InPreD_PRONTO_metadata.txt")
    case = next(row for row in metadata if row["Sample_id"] == report.sample["sampleId"])
    summary = read_text_rows(FIXTURE / "251114_A02134_0115_BHCJCKDRX7_variant_summary.tsv")
    source = next(
        row
        for row in summary
        if row["sample_id"] in {report.sample["sampleId"], report.sample["sampleId"] + "_P"}
    )

    assert report.sample["patientPseudonym"] == case["Study_id"]
    assert report.sample["patientPseudonym"] in html
    for biomarker in report.biomarkers:
        assert biomarker["source"]["rawValue"] == source[biomarker["metricId"].upper()]
    assert "14,9 mut/Mb" in html
    assert "4,13 %" in html
    assert len(report.variants) == 30
