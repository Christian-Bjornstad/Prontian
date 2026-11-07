"""MOL CNV appendix pages use the declared overview, in the requested order."""

import json
from io import BytesIO

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


def test_mol_appends_a2_alone_then_b3_c1_together():
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
    assert "CNV A2" in first.extract_text()
    assert "CNV B3" in second.extract_text() and "CNV C1" in second.extract_text()
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
    assert "CNV A2" not in "".join(page.extract_text() for page in pdf.pages)


def test_unknown_overview_layout_is_disclosed_without_guessing_panels():
    report = overview_report()
    pdf = PdfReader(
        BytesIO(
            render_report_pdf(
                report,
                draft_review(report),
                layout="PRESENTATION",
                export_initials="AB",
                plot_images=panels(8),
            )
        )
    )
    assert "CNV appendix unavailable" in pdf.pages[-1].extract_text()
    assert not pdf.pages[-1].images
