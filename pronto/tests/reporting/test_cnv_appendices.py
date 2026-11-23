"""MOL CNV appendix pages use the declared overview, in the requested order."""

import json
from io import BytesIO

import pytest
from PIL import Image
from pypdf import PdfReader

from pronto.tests.reporting.test_html_review_state import draft_review
from pronto.tests.reporting.test_pronto_output_adapter import build_report
from pronto_report.renderers.report_pdf import render_report_pdf
from pronto_report.serialization import serialize_report_data
from pronto_report.validation import validate_report_data


def overview_report():
    document = json.loads(serialize_report_data(build_report()))
    document["attachments"] = [
        {
            "assetId": "cnv-overview",
            "name": "SYN_CNV_overview_plots.pdf",
            "mediaType": "application/pdf",
            "sha256": "a" * 64,
            "description": "CNV",
        }
    ]
    return validate_report_data(document)


def panels(count=9):
    colors = ["black", "red", "green", "blue", "yellow", "purple", "orange", "gray", "pink"]
    pages = []
    for color in colors[:count]:
        output = BytesIO()
        Image.new("RGB", (300, 120), color).save(output, "PNG")
        pages.append(("image/png", output.getvalue()))
    return {"cnv-overview": tuple(pages)}


def test_mol_appends_source_page_two_alone_then_four_and_five_together():
    report = overview_report()
    pdf = PdfReader(
        BytesIO(
            render_report_pdf(
                report,
                draft_review(report),
                layout="PRESENTATION",
                export_initials="AB",
                plot_images=panels(),
            )
        )
    )
    first, second = pdf.pages[-2:]
    assert "source page 2" in first.extract_text()
    assert "source page 4" in second.extract_text() and "source page 5" in second.extract_text()
    assert all(
        label not in first.extract_text() + second.extract_text() for label in ("A2", "B3", "C1")
    )
    assert len(first.images) == 1 and len(second.images) == 2
    assert first.images[0].image.getpixel((20, 20))[:3] == (255, 0, 0)
    assert {image.image.getpixel((20, 20))[:3] for image in second.images} == {
        (0, 0, 255),
        (255, 255, 0),
    }


def test_esmo_does_not_include_the_mol_appendix():
    report = overview_report()
    pdf = PdfReader(
        BytesIO(
            render_report_pdf(
                report,
                draft_review(report),
                layout="ESMO",
                export_initials="AB",
                plot_images=panels(),
            )
        )
    )
    assert not any(page.images for page in pdf.pages)


@pytest.mark.parametrize(
    ("name", "media_type", "count"),
    [
        ("SYN_CNV_overview_plots.pdf", "application/pdf", 1),
        ("alternative-layout.pdf", "application/pdf", 9),
        ("overview-image.png", "image/png", 1),
    ],
)
def test_alternate_sources_keep_all_pages_in_original_order(name, media_type, count):
    document = json.loads(serialize_report_data(overview_report()))
    document["attachments"][0].update(name=name, mediaType=media_type)
    report = validate_report_data(document)
    pdf = PdfReader(
        BytesIO(
            render_report_pdf(
                report,
                draft_review(report),
                layout="PRESENTATION",
                export_initials="AB",
                plot_images=panels(count),
            )
        )
    )
    for index, page in enumerate(pdf.pages[-count:], start=1):
        text = page.extract_text()
        assert name in text and f"source page {index}" in text
        assert len(page.images) == 1


def test_multiple_cnv_sources_keep_their_names_and_exclude_other_plots():
    document = json.loads(serialize_report_data(overview_report()))
    original = document["attachments"][0]
    document["attachments"].extend(
        [
            dict(original, assetId="second-cnv", name="other-layout.pdf"),
            dict(original, assetId="qc", name="sample-qc.pdf", description="QC"),
        ]
    )
    report = validate_report_data(document)
    images = panels(2)
    images.update({"second-cnv": panels(1)["cnv-overview"], "qc": panels(1)["cnv-overview"]})
    pdf = PdfReader(
        BytesIO(
            render_report_pdf(
                report,
                draft_review(report),
                layout="PRESENTATION",
                export_initials="AB",
                plot_images=images,
            )
        )
    )
    texts = [page.extract_text() for page in pdf.pages]
    assert "SYN_CNV_overview_plots.pdf — source page 1" in texts[-3]
    assert "SYN_CNV_overview_plots.pdf — source page 2" in texts[-2]
    assert "other-layout.pdf — source page 1" in texts[-1]
    assert all("sample-qc.pdf" not in text for text in texts)
