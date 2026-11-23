"""Append documented MOL panels or preserve an alternate overview in source order."""

from io import BytesIO

from reportlab.platypus import Image, PageBreak, Spacer


def overview_assets(report):
    """Select only the declared standard overview, excluding Cancan/other plots."""
    return tuple(
        asset
        for asset in report.attachments
        if str(asset["name"]).casefold().endswith("_cnv_overview_plots.pdf")
        and asset["mediaType"] == "application/pdf"
    )


def appendix_story(report, plot_images, width, height):
    """Fit A2 on one page, then B3/C1 vertically on the next without cropping.

    Input images must already have passed the declared-asset hash check. An
    alternate page count is shown in source order. Ambiguous assets are never
    selected automatically.
    """
    from .report_pdf import _heading, _paragraph

    assets = overview_assets(report)
    pages = plot_images.get(str(assets[0]["assetId"]), ()) if len(assets) == 1 else ()
    if not pages:
        reason = (
            "No standard CNV overview PDF was imported."
            if not assets
            else "No unique CNV overview with available pages was found."
        )
        return [PageBreak(), _heading("CNV appendix unavailable"), _paragraph(reason)]

    def panel(index, label, available_height):
        image = Image(BytesIO(pages[index][1]))
        image._restrictSize(width - 8, available_height - 30)
        image.hAlign = "CENTER"
        return [_heading(label), image]

    if len(pages) != 9:
        return [
            flow
            for index in range(len(pages))
            for flow in [
                PageBreak(),
                *panel(index, f"CNV overview — source page {index + 1}", height - 8),
            ]
        ]

    return [
        PageBreak(),
        *panel(1, "CNV A2 — source page 2", height - 8),
        PageBreak(),
        *panel(3, "CNV B3 — source page 4", (height - 14) / 2),
        Spacer(1, 8),
        *panel(4, "CNV C1 — source page 5", (height - 14) / 2),
    ]
